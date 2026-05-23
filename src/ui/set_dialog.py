"""Dialog for entering per-set point scores of a match (max 5 sets)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QGridLayout, QHBoxLayout, QLabel, QSpinBox,
    QVBoxLayout, QWidget, QMessageBox,
)

from ..models import Match, Player
from ..tournament import derive_match_result


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
        self.setMinimumWidth(520)
        self._build()
        self._load_existing()
        self._refresh_result()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        header = QLabel(f"{self.p1.name}   vs   {self.p2.name}")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(header)

        info = QLabel(
            "Saisis les points marqués par chaque joueur, set par set. "
            "Laisse un set à 0 - 0 si non joué."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        outer.addWidget(info)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        # Header row
        grid.addWidget(self._small_label("Set"), 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self._small_label(self.p1.name), 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self._small_label(""), 0, 2)
        grid.addWidget(self._small_label(self.p2.name), 0, 3, alignment=Qt.AlignmentFlag.AlignCenter)

        for i in range(MAX_SETS):
            lbl = QLabel(f"Set {i + 1}")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(lbl, i + 1, 0)

            s1 = self._spin()
            s2 = self._spin()
            self._p1_spins.append(s1)
            self._p2_spins.append(s2)
            grid.addWidget(s1, i + 1, 1)

            sep = QLabel("-")
            sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(sep, i + 1, 2)

            grid.addWidget(s2, i + 1, 3)

            s1.valueChanged.connect(self._refresh_result)
            s2.valueChanged.connect(self._refresh_result)

        outer.addLayout(grid)

        # Live result preview
        self._result_label = QLabel("Résultat : 0 - 0")
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_label.setStyleSheet(
            "background-color: #1B1B1F; padding: 10px; border-radius: 4px; font-size: 12pt;"
        )
        outer.addWidget(self._result_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    @staticmethod
    def _small_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#C8102E; font-weight: bold;")
        return lbl

    @staticmethod
    def _spin() -> QSpinBox:
        sp = QSpinBox()
        sp.setRange(0, 99)
        sp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sp.setFixedWidth(70)
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
            text = "Résultat : 0 - 0"
        else:
            if w1 > w2:
                text = f"<b>{self.p1.name}</b> {w1} - {w2} {self.p2.name}"
            elif w2 > w1:
                text = f"{self.p1.name} {w1} - {w2} <b>{self.p2.name}</b>"
            else:
                text = f"{self.p1.name} {w1} - {w2} {self.p2.name}   (égalité)"
        if self._result_label is not None:
            self._result_label.setText(text)

    def _on_accept(self):
        # Validate no tied non-empty set
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
