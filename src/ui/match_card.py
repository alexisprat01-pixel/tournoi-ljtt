"""A single match card with score inputs."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ..models import Match, Player


class MatchCard(QFrame):
    """Visual card for one match: shows both players and lets the user enter the score."""

    score_saved = pyqtSignal(int, int, int, bool)  # match_id, score1, score2, played

    def __init__(self, match: Match, p1: Player, p2: Player, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("matchCard")
        self.setProperty("played", match.played)
        self.match = match

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Player 1
        p1_label = QLabel(self._fmt(p1))
        p1_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        p1_label.setMinimumWidth(180)

        self.score1 = QSpinBox()
        self.score1.setRange(0, 5)
        self.score1.setValue(match.score1)
        self.score1.setFixedWidth(56)
        self.score1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        vs = QLabel("–")
        vs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vs.setFixedWidth(12)

        self.score2 = QSpinBox()
        self.score2.setRange(0, 5)
        self.score2.setValue(match.score2)
        self.score2.setFixedWidth(56)
        self.score2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        p2_label = QLabel(self._fmt(p2))
        p2_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        p2_label.setMinimumWidth(180)

        self.btn = QPushButton("Valider" if not match.played else "Modifier")
        self.btn.setObjectName("secondary" if match.played else "")
        self.btn.clicked.connect(self._on_click)

        layout.addWidget(p1_label, 1)
        layout.addWidget(self.score1)
        layout.addWidget(vs)
        layout.addWidget(self.score2)
        layout.addWidget(p2_label, 1)
        layout.addWidget(self.btn)

    @staticmethod
    def _fmt(p: Player) -> str:
        if p.club:
            return f"{p.name}  ({p.club})"
        return p.name

    def _on_click(self):
        s1, s2 = self.score1.value(), self.score2.value()
        played = (s1 != s2) and (max(s1, s2) >= 1)
        self.score_saved.emit(self.match.id, s1, s2, played)
