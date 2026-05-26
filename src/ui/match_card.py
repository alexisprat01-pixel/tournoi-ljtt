"""A single match card — colored table badge + referee + players + score on one line."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QWidget,
)

from ..models import Match, Player
from .set_dialog import SetScoresDialog


# One distinctive colour per table, used for the round badge.
TABLE_COLORS = {
    1: "#C8102E",   # red — club colour
    2: "#1E88E5",   # blue
    3: "#43A047",   # green
}


class MatchCard(QFrame):
    """Read-only single-line match card with a colored table badge."""

    sets_saved = pyqtSignal(int, list)   # match_id, set_scores

    def __init__(
        self,
        match: Match,
        p1: Player,
        p2: Player,
        referee: Player | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("matchCard")
        self.setProperty("played", match.played)
        self.match = match
        self.p1 = p1
        self.p2 = p2
        self.referee = referee

        winner1 = match.played and match.score1 > match.score2
        winner2 = match.played and match.score2 > match.score1

        h = QHBoxLayout(self)
        h.setContentsMargins(16, 12, 16, 12)
        h.setSpacing(14)

        # Colored table pill (T1 rouge, T2 bleu, T3 vert — convention club)
        badge = self._build_table_badge(match.table_number, played=match.played)
        h.addWidget(badge)
        h.addSpacing(6)

        # Referee (or placeholder if unassigned)
        ref_text = f"⚖  {referee.name}" if referee is not None else "⚖  —"
        ref_lbl = QLabel(ref_text)
        ref_lbl.setStyleSheet(
            "color:#B4B4B8; font-size:10pt; background:transparent; "
            "font-family:'Segoe UI Symbol','Segoe UI';"
        )
        ref_lbl.setMinimumWidth(170)
        ref_lbl.setToolTip("Arbitre" if referee is None else f"Arbitre : {referee.name}")
        h.addWidget(ref_lbl)
        h.addSpacing(12)

        # Player 1 (right aligned)
        p1_lbl = QLabel(f"<b>{p1.name}</b>" if winner1 else p1.name)
        p1_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        p1_lbl.setMinimumWidth(180)
        p1_lbl.setContentsMargins(0, 0, 14, 0)   # breathing room before the score
        h.addWidget(p1_lbl, 1)

        # Score (with bold on the winner's count)
        score_lbl = QLabel(self._fmt_score(match, winner1, winner2))
        score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_lbl.setFixedWidth(80)
        score_lbl.setStyleSheet(
            "font-size:14pt; background:transparent; padding: 0 6px;"
        )
        score_lbl.setToolTip(self._fmt_sets_tooltip(match))
        h.addWidget(score_lbl)

        # Player 2 (left aligned)
        p2_lbl = QLabel(f"<b>{p2.name}</b>" if winner2 else p2.name)
        p2_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        p2_lbl.setMinimumWidth(180)
        p2_lbl.setContentsMargins(14, 0, 0, 0)   # breathing room after the score
        h.addWidget(p2_lbl, 1)
        h.addSpacing(8)

        # Action button
        self.btn = QPushButton("Modifier le score" if match.played else "Saisir le score")
        if match.played:
            self.btn.setObjectName("secondary")
        self.btn.clicked.connect(self._open_dialog)
        h.addWidget(self.btn)

    @staticmethod
    def _build_table_badge(table_number: int, played: bool = False) -> QLabel:
        text = f"T{table_number}" if table_number else "?"
        color = TABLE_COLORS.get(table_number, "#6C6C72")
        badge = QLabel(text)
        badge.setFixedHeight(26)
        badge.setMinimumWidth(44)
        badge.setMaximumWidth(56)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Qt QSS does not honour `opacity`; we bake the alpha into the
        # background colour (and text colour) when the match has been played
        # so the pill visually recedes while staying readable.
        if played:
            c = QColor(color)
            bg = f"rgba({c.red()},{c.green()},{c.blue()},128)"
            fg = "rgba(255,255,255,180)"
        else:
            bg = color
            fg = "white"
        badge.setStyleSheet(
            f"background-color:{bg}; color:{fg}; font-weight:700; "
            "font-family:'JetBrains Mono','Consolas',monospace; "
            "font-size:10pt; letter-spacing:1px; border-radius:13px; "
            "padding:0 10px;"
        )
        badge.setToolTip(f"Table {table_number}" if table_number else "Table non assignée")
        return badge

    def _open_dialog(self):
        dlg = SetScoresDialog(self.match, self.p1, self.p2, parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        self.sets_saved.emit(self.match.id, dlg.get_set_scores())

    # ----- formatting helpers -----
    @staticmethod
    def _fmt_score(m: Match, winner1: bool, winner2: bool) -> str:
        if not m.played:
            return "–"
        left = f"<b>{m.score1}</b>" if winner1 else str(m.score1)
        right = f"<b>{m.score2}</b>" if winner2 else str(m.score2)
        return f"{left} - {right}"

    @staticmethod
    def _fmt_sets_tooltip(m: Match) -> str:
        if not m.set_scores:
            return "Aucun set saisi"
        parts = []
        for i, pair in enumerate(m.set_scores, start=1):
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                parts.append(f"Set {i} : {pair[0]} - {pair[1]}")
        return "\n".join(parts) if parts else "Aucun set saisi"
