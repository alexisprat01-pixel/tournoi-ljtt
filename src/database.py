"""SQLite persistence layer."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List

from .models import Match, Player


SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    club  TEXT DEFAULT '',
    pool  TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS matches (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    round_number INTEGER NOT NULL,
    phase        TEXT NOT NULL,
    player1_id   INTEGER NOT NULL,
    player2_id   INTEGER NOT NULL,
    score1       INTEGER DEFAULT 0,
    score2       INTEGER DEFAULT 0,
    played       INTEGER DEFAULT 0,
    pool         TEXT DEFAULT '',
    FOREIGN KEY(player1_id) REFERENCES players(id),
    FOREIGN KEY(player2_id) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._init()

    def _init(self):
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ----- Players -----
    def reset_tournament(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM matches")
            conn.execute("DELETE FROM players")
            conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('players','matches')")

    def insert_player(self, name: str, club: str = "") -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO players(name, club) VALUES(?, ?)", (name, club)
            )
            return cur.lastrowid

    def update_player_pool(self, player_id: int, pool: str):
        with self._connect() as conn:
            conn.execute("UPDATE players SET pool=? WHERE id=?", (pool, player_id))

    def list_players(self) -> List[Player]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, club, pool FROM players ORDER BY id"
            ).fetchall()
        return [Player(id=r["id"], name=r["name"], club=r["club"] or "", pool=r["pool"] or "") for r in rows]

    # ----- Matches -----
    def insert_matches(self, matches: List[Match]) -> List[Match]:
        with self._connect() as conn:
            for m in matches:
                cur = conn.execute(
                    """INSERT INTO matches
                       (round_number, phase, player1_id, player2_id, score1, score2, played, pool)
                       VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                    (m.round_number, m.phase, m.player1_id, m.player2_id,
                     m.score1, m.score2, int(m.played), m.pool),
                )
                m.id = cur.lastrowid
        return matches

    def update_match_score(self, match_id: int, score1: int, score2: int, played: bool):
        with self._connect() as conn:
            conn.execute(
                "UPDATE matches SET score1=?, score2=?, played=? WHERE id=?",
                (score1, score2, int(played), match_id),
            )

    def list_matches(self) -> List[Match]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT id, round_number, phase, player1_id, player2_id,
                          score1, score2, played, pool
                   FROM matches ORDER BY round_number, id"""
            ).fetchall()
        return [Match(
            id=r["id"],
            round_number=r["round_number"],
            phase=r["phase"],
            player1_id=r["player1_id"],
            player2_id=r["player2_id"],
            score1=r["score1"] or 0,
            score2=r["score2"] or 0,
            played=bool(r["played"]),
            pool=r["pool"] or "",
        ) for r in rows]

    def delete_matches_from_round(self, from_round: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM matches WHERE round_number >= ?", (from_round,))

    # ----- Settings -----
    def set_setting(self, key: str, value: str):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default
