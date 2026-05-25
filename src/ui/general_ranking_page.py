"""Overall standings page — all 12 players, all matches, tie-break rules applied."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QFont, QFontMetrics, QPainterPath, QRegion
from PyQt6.QtWidgets import (
    QFrame, QHeaderView, QLabel, QSizePolicy, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ..models import Match, Player, PlayerStanding
from ..tournament import compute_standings
from .styles import RED, TEXT


# Generous row padding so the table fills the page nicely.
ROW_VERTICAL_PADDING = 22


class GeneralRankingPage(QWidget):
    """Single page showing the overall tournament standings."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(12)

        title = QLabel(
            f"<span style='color:{TEXT};'>Classement</span> "
            f"<span style='color:{RED};'>général</span>"
        )
        title.setObjectName("h1")
        outer.addWidget(title)

        self.subtitle = QLabel("")
        self.subtitle.setObjectName("muted")
        self.subtitle.setWordWrap(True)
        outer.addWidget(self.subtitle)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 8, 0, 0)
        outer.addWidget(self._content, 1)

    def set_data(self, players: list[Player], matches: list[Match]):
        # Clear existing content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        played_count = sum(1 for m in matches if m.played)
        total = len(matches)

        if total == 0:
            self.subtitle.setText(
                "Les poules n'ont pas encore été calculées. Saisis les 12 joueurs "
                "et clique sur \"Calculer les poules\" pour démarrer."
            )
            return
        if played_count == 0:
            self.subtitle.setText(
                "Aucun match joué pour le moment. Le classement apparaîtra ici "
                "dès que des scores seront saisis."
            )
            return

        self.subtitle.setText(
            f"{played_count} match{'s' if played_count > 1 else ''} joué"
            f"{'s' if played_count > 1 else ''} sur {total}. "
            "Départage : 2 ex-aequo → face-à-face ; 3+ ex-aequo → diff sets ; "
            "puis face-à-face entre 2 restants."
        )

        standings = compute_standings(players, matches)
        self._content_layout.addWidget(self._wrap_table(self._make_table(standings)))
        # No stretch below — let the table expand to the full available area.

    @staticmethod
    def _wrap_table(table: QTableWidget) -> QFrame:
        """Same rounded wrap as the pool standings — keeps a coherent look."""

        class _RoundedWrap(QFrame):
            def __init__(self, radius: int = 10):
                super().__init__()
                self.setObjectName("tableWrap")
                self._radius = radius

            def resizeEvent(self, event):
                super().resizeEvent(event)
                path = QPainterPath()
                path.addRoundedRect(
                    QRectF(self.rect()), float(self._radius), float(self._radius)
                )
                self.setMask(QRegion(path.toFillPolygon().toPolygon()))

        wrap = _RoundedWrap(radius=10)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(1, 1, 1, 1)
        lay.setSpacing(0)
        lay.addWidget(table)
        wrap.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        return wrap

    @staticmethod
    def _make_table(standings: list[PlayerStanding]) -> QTableWidget:
        table = QTableWidget(len(standings), 6)
        table.setHorizontalHeaderLabels(["#", "Joueur", "J", "V", "Pts", "Diff sets"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # Larger, semi-bold typography for the player-name column.
        name_font = QFont("Segoe UI", 13, QFont.Weight.DemiBold)
        for row, st in enumerate(standings):
            items = [
                QTableWidgetItem(str(row + 1)),
                QTableWidgetItem(st.player.name),
                QTableWidgetItem(str(st.played)),
                QTableWidgetItem(str(st.wins)),
                QTableWidgetItem(str(st.points)),
                QTableWidgetItem(f"{st.set_diff:+d}"),
            ]
            items[1].setFont(name_font)
            for col, item in enumerate(items):
                if col != 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, col, item)

        header = table.horizontalHeader()
        for col in range(table.columnCount()):
            mode = (
                QHeaderView.ResizeMode.Stretch if col == 1
                else QHeaderView.ResizeMode.ResizeToContents
            )
            header.setSectionResizeMode(col, mode)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Deterministic, generous row height — fills the page nicely.
        fm = QFontMetrics(name_font)
        row_h = fm.height() + ROW_VERTICAL_PADDING
        vh = table.verticalHeader()
        vh.setDefaultSectionSize(row_h)
        vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        header_fm = QFontMetrics(table.font())
        header_h = max(header.sizeHint().height(), header_fm.height() + 18)
        header.setFixedHeight(header_h)
        table.setFixedHeight(
            header_h + row_h * table.rowCount() + 2 * table.frameWidth()
        )

        # Transparent viewport so the rounded wrap shows through.
        table.viewport().setAutoFillBackground(False)
        table.viewport().setStyleSheet("background: transparent;")
        table.setFrameShape(QFrame.Shape.NoFrame)
        return table
