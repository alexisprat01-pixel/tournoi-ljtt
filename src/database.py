"""SQLite persistence layer — multi-tournament."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import Match, Player, Tournament


# Tables only — runs before migration, so it must NOT reference columns
# that the migration is responsible for adding.
SCHEMA_TABLES = """
CREATE TABLE IF NOT EXISTS tournaments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    tournament_type TEXT DEFAULT 'top12',
    event_date      TEXT DEFAULT '',
    notes           TEXT DEFAULT '',
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    name          TEXT NOT NULL,
    points        INTEGER DEFAULT 0,
    pool          TEXT DEFAULT '',
    FOREIGN KEY(tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS matches (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tournament_id INTEGER NOT NULL,
    round_number  INTEGER NOT NULL,
    phase         TEXT NOT NULL,
    player1_id    INTEGER NOT NULL,
    player2_id    INTEGER NOT NULL,
    score1        INTEGER DEFAULT 0,
    score2        INTEGER DEFAULT 0,
    played        INTEGER DEFAULT 0,
    pool          TEXT DEFAULT '',
    set_scores    TEXT DEFAULT '[]',
    table_number  INTEGER DEFAULT 0,
    referee_id    INTEGER DEFAULT 0,
    FOREIGN KEY(tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
    FOREIGN KEY(player1_id) REFERENCES players(id),
    FOREIGN KEY(player2_id) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

# Indexes — created after migration so the columns they reference exist.
SCHEMA_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_players_tournament ON players(tournament_id);
CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches(tournament_id);
"""


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._init()

    def _init(self):
        with self._connect() as conn:
            conn.executescript(SCHEMA_TABLES)
            self._migrate_v1_if_needed(conn)
            conn.executescript(SCHEMA_INDEXES)

    def _migrate_v1_if_needed(self, conn: sqlite3.Connection):
        """Bring legacy schemas up to current shape:
        - v1: no tournament_id, no points column → add both
        - v2: tournament_id present but no points → add points
        Any data left over from a previous run is wrapped in a 'Tournoi importé' record.
        """
        players_cols = {r["name"] for r in conn.execute("PRAGMA table_info(players)").fetchall()}
        matches_cols = {r["name"] for r in conn.execute("PRAGMA table_info(matches)").fetchall()}
        tournaments_cols = {r["name"] for r in conn.execute("PRAGMA table_info(tournaments)").fetchall()}

        # --- tournament_type (v5 → v6, generalise app to multiple formats) ---
        if "tournament_type" not in tournaments_cols:
            conn.execute("ALTER TABLE tournaments ADD COLUMN tournament_type TEXT DEFAULT 'top12'")
            conn.execute("UPDATE tournaments SET tournament_type='top12' WHERE tournament_type IS NULL")

        # --- tournament_id (v1 → v2) ---
        added_tournament_col = False
        if "tournament_id" not in players_cols:
            conn.execute("ALTER TABLE players ADD COLUMN tournament_id INTEGER")
            added_tournament_col = True
        if "tournament_id" not in matches_cols:
            conn.execute("ALTER TABLE matches ADD COLUMN tournament_id INTEGER")

        # --- points (v2 → v3, replaces club) ---
        if "points" not in players_cols:
            conn.execute("ALTER TABLE players ADD COLUMN points INTEGER DEFAULT 0")

        # --- set_scores (v3 → v4, per-set point scores) ---
        if "set_scores" not in matches_cols:
            conn.execute("ALTER TABLE matches ADD COLUMN set_scores TEXT DEFAULT '[]'")

        # --- table_number / referee_id (v4 → v5, equity scheduling) ---
        if "table_number" not in matches_cols:
            conn.execute("ALTER TABLE matches ADD COLUMN table_number INTEGER DEFAULT 0")
        if "referee_id" not in matches_cols:
            conn.execute("ALTER TABLE matches ADD COLUMN referee_id INTEGER DEFAULT 0")

        if not added_tournament_col:
            return

        # First-time tournament_id migration: wrap any pre-existing rows in a placeholder tournament.
        old_players = conn.execute("SELECT COUNT(*) AS n FROM players").fetchone()["n"]
        if old_players == 0:
            return

        now = _now()
        cur = conn.execute(
            "INSERT INTO tournaments(name, event_date, notes, created_at, updated_at) VALUES(?,?,?,?,?)",
            ("Tournoi importé", "", "Migré automatiquement depuis l'ancienne version", now, now),
        )
        tid = cur.lastrowid
        conn.execute("UPDATE players SET tournament_id = ? WHERE tournament_id IS NULL", (tid,))
        conn.execute("UPDATE matches SET tournament_id = ? WHERE tournament_id IS NULL", (tid,))

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

    # ----- Tournaments -----
    def create_tournament(self, name: str, event_date: str = "", notes: str = "",
                          tournament_type: str = "top12") -> Tournament:
        now = _now()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO tournaments(name, tournament_type, event_date, notes, created_at, updated_at) "
                "VALUES(?,?,?,?,?,?)",
                (name, tournament_type, event_date, notes, now, now),
            )
            return Tournament(id=cur.lastrowid, name=name, tournament_type=tournament_type,
                              event_date=event_date, notes=notes,
                              created_at=now, updated_at=now)

    def list_tournaments(self) -> List[Tournament]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, tournament_type, event_date, notes, created_at, updated_at "
                "FROM tournaments ORDER BY datetime(updated_at) DESC"
            ).fetchall()
        return [Tournament(
            id=r["id"], name=r["name"],
            tournament_type=r["tournament_type"] or "top12",
            event_date=r["event_date"] or "", notes=r["notes"] or "",
            created_at=r["created_at"], updated_at=r["updated_at"],
        ) for r in rows]

    def get_tournament(self, tournament_id: int) -> Optional[Tournament]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, tournament_type, event_date, notes, created_at, updated_at "
                "FROM tournaments WHERE id=?", (tournament_id,)
            ).fetchone()
        if row is None:
            return None
        return Tournament(
            id=row["id"], name=row["name"],
            tournament_type=row["tournament_type"] or "top12",
            event_date=row["event_date"] or "", notes=row["notes"] or "",
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def update_tournament(self, tournament_id: int, name: str, event_date: str, notes: str,
                          tournament_type: str | None = None):
        with self._connect() as conn:
            if tournament_type is None:
                conn.execute(
                    "UPDATE tournaments SET name=?, event_date=?, notes=?, updated_at=? WHERE id=?",
                    (name, event_date, notes, _now(), tournament_id),
                )
            else:
                conn.execute(
                    "UPDATE tournaments SET name=?, tournament_type=?, event_date=?, notes=?, updated_at=? "
                    "WHERE id=?",
                    (name, tournament_type, event_date, notes, _now(), tournament_id),
                )

    def delete_tournament(self, tournament_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM matches WHERE tournament_id=?", (tournament_id,))
            conn.execute("DELETE FROM players WHERE tournament_id=?", (tournament_id,))
            conn.execute("DELETE FROM tournaments WHERE id=?", (tournament_id,))

    def touch_tournament(self, tournament_id: int):
        with self._connect() as conn:
            conn.execute("UPDATE tournaments SET updated_at=? WHERE id=?", (_now(), tournament_id))

    # ----- Players -----
    def reset_tournament_data(self, tournament_id: int):
        """Clears players + matches but keeps the tournament record."""
        with self._connect() as conn:
            conn.execute("DELETE FROM matches WHERE tournament_id=?", (tournament_id,))
            conn.execute("DELETE FROM players WHERE tournament_id=?", (tournament_id,))
            conn.execute("UPDATE tournaments SET updated_at=? WHERE id=?", (_now(), tournament_id))

    def insert_player(self, tournament_id: int, name: str, points: int = 0) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO players(tournament_id, name, points) VALUES(?,?,?)",
                (tournament_id, name, points),
            )
            return cur.lastrowid

    def update_player_pool(self, player_id: int, pool: str):
        with self._connect() as conn:
            conn.execute("UPDATE players SET pool=? WHERE id=?", (pool, player_id))

    def list_players(self, tournament_id: int) -> List[Player]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, points, pool FROM players WHERE tournament_id=? ORDER BY id",
                (tournament_id,),
            ).fetchall()
        return [Player(
            id=r["id"], name=r["name"],
            points=r["points"] or 0, pool=r["pool"] or "",
        ) for r in rows]

    # ----- Matches -----
    def insert_matches(self, tournament_id: int, matches: List[Match]) -> List[Match]:
        with self._connect() as conn:
            for m in matches:
                cur = conn.execute(
                    """INSERT INTO matches
                       (tournament_id, round_number, phase, player1_id, player2_id,
                        score1, score2, played, pool, set_scores, table_number, referee_id)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (tournament_id, m.round_number, m.phase, m.player1_id, m.player2_id,
                     m.score1, m.score2, int(m.played), m.pool, json.dumps(m.set_scores or []),
                     m.table_number or 0, m.referee_id or 0),
                )
                m.id = cur.lastrowid
            conn.execute("UPDATE tournaments SET updated_at=? WHERE id=?", (_now(), tournament_id))
        return matches

    def update_match_assignment(self, match_id: int, table_number: int, referee_id: int):
        with self._connect() as conn:
            conn.execute(
                "UPDATE matches SET table_number=?, referee_id=? WHERE id=?",
                (table_number, referee_id, match_id),
            )

    def update_match_sets(self, match_id: int, set_scores: list, score1: int, score2: int, played: bool):
        """Save the per-set scores along with their derived totals."""
        with self._connect() as conn:
            row = conn.execute("SELECT tournament_id FROM matches WHERE id=?", (match_id,)).fetchone()
            conn.execute(
                "UPDATE matches SET set_scores=?, score1=?, score2=?, played=? WHERE id=?",
                (json.dumps(set_scores), score1, score2, int(played), match_id),
            )
            if row is not None:
                conn.execute("UPDATE tournaments SET updated_at=? WHERE id=?", (_now(), row["tournament_id"]))

    def list_matches(self, tournament_id: int) -> List[Match]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT id, round_number, phase, player1_id, player2_id,
                          score1, score2, played, pool, set_scores,
                          table_number, referee_id
                   FROM matches WHERE tournament_id=? ORDER BY round_number, id""",
                (tournament_id,),
            ).fetchall()
        results: List[Match] = []
        for r in rows:
            raw = r["set_scores"] or "[]"
            try:
                sets = json.loads(raw)
                if not isinstance(sets, list):
                    sets = []
            except (json.JSONDecodeError, TypeError):
                sets = []
            results.append(Match(
                id=r["id"],
                round_number=r["round_number"],
                phase=r["phase"],
                player1_id=r["player1_id"],
                player2_id=r["player2_id"],
                score1=r["score1"] or 0,
                score2=r["score2"] or 0,
                played=bool(r["played"]),
                pool=r["pool"] or "",
                set_scores=sets,
                table_number=r["table_number"] or 0,
                referee_id=r["referee_id"] or 0,
            ))
        return results

    def delete_matches_from_round(self, tournament_id: int, from_round: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM matches WHERE tournament_id=? AND round_number >= ?",
                         (tournament_id, from_round))

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
