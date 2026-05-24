"""Dialog for entering per-set point scores of a match (max 5 sets)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ..models import Match, Player
from ..tournament import derive_match_result
from .styles import (
    CARD_RADIUS, GREY, GREY_DARK, GREY_LIGHT, RED, TEXT, TEXT_DIM,
)


MAX_SETS = 5


class SetScoresDialog(QDialog):
    """Lets the user enter the points each player scored in each set.

    A set with both fields at 0 is treated as 'not played'. A set with equal
    non-zero scores is invalid (a set must have a winner).
    """

    def __init__(self, match: Match, p1: Player, p2: Player, parent: QWidget | None = None):
        super().__init__(parent)
        self.match = match
        self.p1 = p1
        self.p2 = p2
        self._p1_spins: list[QSpinBox] = []
        self._p2_spins: list[QSpinBox] = []
        self._result_label: QLabel | None = None

        self.setWindowTitle("Score du match")
        self.setMinimumWidth(560)
        self._build()
        self._load_existing()
        self._refresh_result()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)

        # Bicolor title — consistent with the rest of the app
        title = QLabel(
            f"<span style='color:{TEXT};'>Score du</span> "
            f"<span style='color:{RED};'>match</span>"
        )
        title.setStyleSheet(
            "font-size: 20pt; font-weight: bold; background: transparent;"
        )
        outer.addWidget(title)

        # Match header (player names)
        match_lbl = QLabel(f"{self.p1.name}   vs   {self.p2.name}")
        match_lbl.setStyleSheet(
            f"font-size: 13pt; color: {TEXT}; background: transparent; font-weight: bold;"
        )
        match_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(match_lbl)

        info = QLabel(
            "Saisis les points marqués par chaque joueur, set par set. "
            "Laisse un set à 0 - 0 si non joué."
        )
        info.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        info.setWordWrap(True)
        outer.addWidget(info)

        # Grid of sets inside a card to give it some structure
        card = QFrame()
        card.setStyleSheet(
            f"background-color: {GREY}; border: 1px solid {GREY_LIGHT}; "
            f"border-radius: {CARD_RADIUS}px;"
        )
        grid = QGridLayout(card)
        grid.setContentsMargins(18, 14, 18, 14)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        # Column headers
        grid.addWidget(self._header_label("Set"), 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self._header_label(self.p1.name), 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(QLabel(""), 0, 2)
        grid.addWidget(self._header_label(self.p2.name), 0, 3, alignment=Qt.AlignmentFlag.AlignCenter)

        for i in range(MAX_SETS):
            lbl = QLabel(f"Set {i + 1}")
            lbl.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(lbl, i + 1, 0)

            s1 = self._spin()
            s2 = self._spin()
            self._p1_spins.append(s1)
            self._p2_spins.append(s2)
            grid.addWidget(s1, i + 1, 1)

            sep = QLabel("-")
            sep.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
            sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(sep, i + 1, 2)

            grid.addWidget(s2, i + 1, 3)

            s1.valueChanged.connect(self._refresh_result)
            s2.valueChanged.connect(self._refresh_result)
        outer.addWidget(card)

        # Live result preview — full-width pill banner
        self._result_label = QLabel("Résultat : 0 - 0")
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_label.setStyleSheet(
            f"background-color: {GREY_DARK}; color: {TEXT}; "
            f"padding: 14px; border: 1px solid {GREY_LIGHT}; "
            f"border-radius: {CARD_RADIUS}px; font-size: 13pt;"
        )
        outer.addWidget(self._result_label)

        # Buttons row — plain QPushButtons get the pill style via QSS
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

    @staticmethod
    def _header_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {RED}; font-weight: bold; font-size: 9pt; "
            "background: transparent; letter-spacing: 1px;"
        )
        return lbl

    @staticmethod
    def _spin() -> QSpinBox:
        sp = QSpinBox()
        sp.setRange(0, 99)
        sp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sp.setFixedWidth(76)
        sp.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        return sp

    def _load_existing(self):
        for i in range(MAX_SETS):
            if i < len(self.match.set_scores):
                pair = self.match.set_scores[i]
                if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                    self._p1_spins[i].setValue(int(pair[0]))
                    self._p2_spins[i].setValue(int(pair[1]))

    def _collect(self) -> list[list[int]]:
        sets: list[list[int]] = []
        for s1, s2 in zip(self._p1_spins, self._p2_spins):
            v1, v2 = s1.value(), s2.value()
            if v1 == 0 and v2 == 0:
                continue
            sets.append([v1, v2])
        return sets

    def _refresh_result(self):
        sets = self._collect()
        w1, w2, played = derive_match_result(sets)
        if not played:
            text = (
                f"<span style='color:{TEXT_DIM};'>Aucun set saisi pour le moment</span>"
            )
        elif w1 > w2:
            text = (
                f"<span style='color:{RED}; font-weight:bold;'>{self.p1.name}</span>"
                f"  <b>{w1}</b> - {w2}  {self.p2.name}"
            )
        elif w2 > w1:
            text = (
                f"{self.p1.name}  {w1} - <b>{w2}</b>  "
                f"<span style='color:{RED}; font-weight:bold;'>{self.p2.name}</span>"
            )
        else:
            text = f"{self.p1.name}  {w1} - {w2}  {self.p2.name}   (égalité)"
        if self._result_label is not None:
            self._result_label.setText(text)

    def _on_accept(self):
        for i, (s1, s2) in enumerate(zip(self._p1_spins, self._p2_spins), start=1):
            v1, v2 = s1.value(), s2.value()
            if v1 != 0 or v2 != 0:
                if v1 == v2:
                    QMessageBox.warning(
                        self, "Set invalide",
                        f"Le set {i} ne peut pas se terminer sur une égalité ({v1} - {v2}).",
                    )
                    return
        self.accept()

    def get_set_scores(self) -> list[list[int]]:
        return self._collect()
