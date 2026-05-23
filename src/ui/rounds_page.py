"""Rounds page — displays all rounds with match cards and standings."""
from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton, QScrollArea,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..models import Match, Player, PlayerStanding
from ..tournament import compute_standings
from .match_card import MatchCard


class RoundsPage(QWidget):
    """Shows the 5 pool rounds + 6 cross rounds."""

    score_changed = pyqtSignal(int, int, int, bool)        # match_id, s1, s2, played
    generate_cross_requested = pyqtSignal()                # user clicks "Générer phase finale"

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._players: dict[int, Player] = {}
        self._matches: list[Match] = []
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Header bar with title + action button
        header = QHBoxLayout()
        header.setContentsMargins(32, 24, 32, 0)

        self.title = QLabel("Phase de poules")
        self.title.setObjectName("h1")
        header.addWidget(self.title)
        header.addStretch()

        self.action_btn = QPushButton("Générer la phase finale")
        self.action_btn.setVisible(False)
        self.action_btn.clicked.connect(self.generate_cross_requested.emit)
        header.addWidget(self.action_btn)
        outer.addLayout(header)

        self.subtitle = QLabel("")
        self.subtitle.setObjectName("muted")
        self.subtitle.setContentsMargins(32, 0, 32, 0)
        outer.addWidget(self.subtitle)

        # Scrollable content
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(32, 16, 32, 24)
        self.content_layout.setSpacing(12)
        self.content_layout.addStretch()
        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll, 1)

    def set_data(self, players: list[Player], matches: list[Match]):
        self._players = {p.id: p for p in players}
        self._matches = matches
        self._render()

    def _clear_layout(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _render(self):
        self._clear_layout()

        pool_rounds = [m for m in self._matches if m.phase == "pool"]
        cross_rounds = [m for m in self._matches if m.phase == "cross"]

        pools_complete = bool(pool_rounds) and all(m.played for m in pool_rounds)
        has_cross = bool(cross_rounds)

        if has_cross:
            self.title.setText("Tournoi Top12")
            self.subtitle.setText("Phase de poules terminée. Phase finale en cours.")
            self.action_btn.setVisible(False)
        elif pools_complete:
            self.title.setText("Phase de poules — terminée")
            self.subtitle.setText("Tous les matchs des poules sont joués. Tu peux générer la phase finale.")
            self.action_btn.setVisible(True)
        else:
            self.title.setText("Phase de poules")
            self.subtitle.setText("Tours 1 à 5 — chaque joueur rencontre les 5 autres de sa poule.")
            self.action_btn.setVisible(False)

        # Render pool rounds 1..5
        max_pool_round = max((m.round_number for m in pool_rounds), default=0)
        for r in range(1, max_pool_round + 1):
            self._add_round_header(f"Tour {r}", phase="pool")
            round_matches = [m for m in pool_rounds if m.round_number == r]
            # Group by pool for readability
            for pool in ("A", "B"):
                pool_matches = [m for m in round_matches if m.pool == pool]
                if pool_matches:
                    self._add_subheader(f"Poule {pool}")
                    for m in pool_matches:
                        self._add_match(m)

        # Intermediate / final standings
        if pool_rounds:
            self._add_round_header("Classement des poules", phase="ranking")
            standings_box = QHBoxLayout()
            for pool in ("A", "B"):
                box = QVBoxLayout()
                lbl = QLabel(f"Poule {pool}")
                lbl.setObjectName("h2")
                box.addWidget(lbl)
                box.addWidget(self._standings_table(
                    compute_standings(self._players.values(), self._matches, pool=pool, max_round=5)
                ))
                container = QWidget()
                container.setLayout(box)
                standings_box.addWidget(container)
            wrap = QWidget()
            wrap.setLayout(standings_box)
            self.content_layout.addWidget(wrap)

        # Cross rounds 6..11
        if cross_rounds:
            max_cross_round = max(m.round_number for m in cross_rounds)
            for r in range(6, max_cross_round + 1):
                label = f"Tour {r}"
                if r == 11:
                    label += "  —  finale par rang"
                self._add_round_header(label, phase="cross")
                round_matches = [m for m in cross_rounds if m.round_number == r]
                for m in round_matches:
                    self._add_match(m)

        # Final standings if all matches played
        if self._matches and all(m.played for m in self._matches):
            self._add_round_header("Classement final", phase="final")
            self.content_layout.addWidget(self._standings_table(
                compute_standings(self._players.values(), self._matches)
            ))

        self.content_layout.addStretch()

    def _add_round_header(self, text: str, phase: str):
        lbl = QLabel(text)
        lbl.setObjectName("h2")
        self.content_layout.addWidget(lbl)

    def _add_subheader(self, text: str):
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#B4B4B8; font-weight:bold; padding-top:4px;")
        self.content_layout.addWidget(lbl)

    def _add_match(self, m: Match):
        p1 = self._players.get(m.player1_id)
        p2 = self._players.get(m.player2_id)
        if p1 is None or p2 is None:
            return
        card = MatchCard(m, p1, p2)
        card.score_saved.connect(self.score_changed.emit)
        self.content_layout.addWidget(card)

    def _standings_table(self, standings: list[PlayerStanding]) -> QTableWidget:
        table = QTableWidget(len(standings), 7)
        table.setHorizontalHeaderLabels(["#", "Joueur", "Club", "J", "V", "Pts", "Diff sets"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for row, st in enumerate(standings):
            items = [
                QTableWidgetItem(str(row + 1)),
                QTableWidgetItem(st.player.name),
                QTableWidgetItem(st.player.club),
                QTableWidgetItem(str(st.played)),
                QTableWidgetItem(str(st.wins)),
                QTableWidgetItem(str(st.points)),
                QTableWidgetItem(f"{st.set_diff:+d}"),
            ]
            for col, item in enumerate(items):
                if col != 1 and col != 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, col, item)
        table.resizeColumnsToContents()
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(40 + 36 * len(standings))
        return table
