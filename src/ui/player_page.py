"""Player entry page — 12 names + points, then trigger pool draw."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from .dialogs import confirm
from .styles import RED, TEXT


class PlayerPage(QWidget):
    # Emits list of (name: str, points: int)
    pools_drawn = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.name_edits: list[QLineEdit] = []
        self.points_edits: list[QSpinBox] = []
        self._has_pools = False
        self._build()
        self.set_state(has_pools=False, has_played_matches=False)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(12)

        title = QLabel(
            f"<span style='color:{TEXT};'>Saisie des</span> "
            f"<span style='color:{RED};'>joueurs</span>"
        )
        title.setObjectName("h1")
        outer.addWidget(title)

        self.subtitle = QLabel("")
        self.subtitle.setObjectName("muted")
        self.subtitle.setWordWrap(True)
        outer.addWidget(self.subtitle)

        card = QFrame()
        card.setObjectName("card")
        grid = QGridLayout(card)
        grid.setContentsMargins(20, 20, 20, 20)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        grid.addWidget(self._header("#"), 0, 0)
        grid.addWidget(self._header("Nom du joueur"), 0, 1)
        grid.addWidget(self._header("Points"), 0, 2)

        for i in range(12):
            num = QLabel(f"{i + 1}")
            num.setFixedWidth(32)
            num.setAlignment(Qt.AlignmentFlag.AlignCenter)

            name = QLineEdit()
            name.setPlaceholderText("Nom Prénom")
            self.name_edits.append(name)

            points = QSpinBox()
            points.setRange(0, 9999)
            points.setSingleStep(10)
            points.setAlignment(Qt.AlignmentFlag.AlignCenter)
            points.setFixedWidth(110)
            points.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            self.points_edits.append(points)

            grid.addWidget(num, i + 1, 0)
            grid.addWidget(name, i + 1, 1)
            grid.addWidget(points, i + 1, 2)

        grid.setColumnStretch(1, 1)
        outer.addWidget(card)

        actions = QHBoxLayout()
        actions.addStretch()
        self.draw_btn = QPushButton("Calculer les poules")
        self.draw_btn.clicked.connect(self._on_draw)
        actions.addWidget(self.draw_btn)
        outer.addLayout(actions)
        outer.addStretch()

    @staticmethod
    def _header(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#C8102E; font-weight:bold;")
        return lbl

    def _on_draw(self):
        players: list[tuple[str, int]] = []
        for name_edit, points_edit in zip(self.name_edits, self.points_edits):
            name = name_edit.text().strip()
            points = points_edit.value()
            if not name:
                QMessageBox.warning(
                    self, "Joueurs incomplets",
                    "Tu dois renseigner les 12 noms de joueurs avant de calculer les poules.",
                )
                return
            players.append((name, points))

        names_lower = [n.lower() for n, _ in players]
        if len(set(names_lower)) != 12:
            QMessageBox.warning(
                self, "Doublons",
                "Deux joueurs ont le même nom. Merci de différencier (prénom, surnom...).",
            )
            return

        all_points = [p for _, p in players]
        if len(set(all_points)) < 12:
            if not confirm(
                self, "Joueurs à égalité de points",
                "Deux joueurs ou plus ont le même nombre de points. "
                "Le départage se fera alphabétiquement. Continuer ?",
                default_yes=True,
            ):
                return

        # Reorder the on-screen entries by points DESC so the user sees the final
        # ranking before confirming. The row numbers (1..12) become the actual ranks
        # used by the pool seeding.
        players_ranked = self._sort_by_points(players)
        self._apply_to_inputs(players_ranked)

        if self._has_pools:
            msg = (
                "Les joueurs viennent d'être reclassés par points. "
                "Le tirage actuel des poules et les matchs (sans score) vont être remplacés. "
                "Continuer ?"
            )
        else:
            msg = (
                "Les joueurs viennent d'être classés par points. "
                "Les 2 poules vont être calculées et les 5 premiers tours générés. Continuer ?"
            )
        if not confirm(self, "Confirmer", msg):
            return

        self.pools_drawn.emit(players_ranked)

    def load_players(self, players: list[tuple[str, int]]):
        # Always display players sorted by points DESC so the row number = rank.
        self._apply_to_inputs(self._sort_by_points(players))

    @staticmethod
    def _sort_by_points(players: list[tuple[str, int]]) -> list[tuple[str, int]]:
        return sorted(players, key=lambda x: (-x[1], x[0].lower()))

    def _apply_to_inputs(self, players: list[tuple[str, int]]):
        for (name, points), n_edit, p_edit in zip(players, self.name_edits, self.points_edits):
            n_edit.setText(name)
            p_edit.setValue(points)

    def set_state(self, *, has_pools: bool, has_played_matches: bool):
        """Configure the page based on tournament progression.

        - has_pools=False, has_played_matches=False  → initial entry
        - has_pools=True,  has_played_matches=False  → editable, button recalculates
        - has_played_matches=True                    → fully locked
        """
        self._has_pools = has_pools
        locked = has_played_matches

        for edit in self.name_edits:
            edit.setReadOnly(locked)
        for sp in self.points_edits:
            sp.setReadOnly(locked)

        if locked:
            self.subtitle.setText(
                "Un ou plusieurs matchs ont déjà un score. La liste des joueurs est verrouillée."
            )
            self.draw_btn.setEnabled(False)
            self.draw_btn.setText("Tournoi en cours — modifications verrouillées")
        elif has_pools:
            self.subtitle.setText(
                "Tu peux encore modifier les joueurs tant qu'aucun score n'est saisi. "
                "Clique sur \"Recalculer les poules\" pour appliquer les modifications."
            )
            self.draw_btn.setEnabled(True)
            self.draw_btn.setText("Recalculer les poules")
        else:
            self.subtitle.setText(
                "Renseigne les 12 joueurs et leur nombre de points. "
                "Les poules seront calculées automatiquement "
                "(A : rangs 1, 4, 5, 8, 9, 12 — B : les autres)."
            )
            self.draw_btn.setEnabled(True)
            self.draw_btn.setText("Calculer les poules")
