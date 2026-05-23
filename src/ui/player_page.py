"""Player entry page — 12 line edits + 'Tirer les poules' button."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QVBoxLayout, QWidget, QFrame,
)


class PlayerPage(QWidget):
    pools_drawn = pyqtSignal(list)  # list of (name, club) tuples in display order

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.name_edits: list[QLineEdit] = []
        self.club_edits: list[QLineEdit] = []
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(12)

        title = QLabel("Saisie des joueurs")
        title.setObjectName("h1")
        outer.addWidget(title)

        subtitle = QLabel("Renseigne les 12 joueurs. Le club est optionnel.")
        subtitle.setObjectName("muted")
        outer.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("card")
        grid = QGridLayout(card)
        grid.setContentsMargins(20, 20, 20, 20)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        # Header
        grid.addWidget(self._header("#"), 0, 0)
        grid.addWidget(self._header("Nom du joueur"), 0, 1)
        grid.addWidget(self._header("Club"), 0, 2)

        for i in range(12):
            num = QLabel(f"{i + 1}")
            num.setFixedWidth(32)
            num.setAlignment(Qt.AlignmentFlag.AlignCenter)

            name = QLineEdit()
            name.setPlaceholderText("Nom Prénom")
            self.name_edits.append(name)

            club = QLineEdit()
            club.setPlaceholderText("Club (optionnel)")
            self.club_edits.append(club)

            grid.addWidget(num, i + 1, 0)
            grid.addWidget(name, i + 1, 1)
            grid.addWidget(club, i + 1, 2)

        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 1)
        outer.addWidget(card)

        # Actions
        actions = QHBoxLayout()
        actions.addStretch()
        self.draw_btn = QPushButton("Tirer les poules")
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
        players: list[tuple[str, str]] = []
        for name_edit, club_edit in zip(self.name_edits, self.club_edits):
            name = name_edit.text().strip()
            club = club_edit.text().strip()
            if not name:
                QMessageBox.warning(
                    self, "Joueurs incomplets",
                    "Tu dois renseigner les 12 noms de joueurs avant de tirer les poules.",
                )
                return
            players.append((name, club))

        # Check uniqueness
        names_lower = [n.lower() for n, _ in players]
        if len(set(names_lower)) != 12:
            QMessageBox.warning(
                self, "Doublons",
                "Deux joueurs ont le même nom. Merci de différencier (prénom, surnom...).",
            )
            return

        confirm = QMessageBox.question(
            self, "Confirmer",
            "Le tirage va créer les 2 poules et générer les 5 premiers tours. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.pools_drawn.emit(players)

    def load_players(self, players: list[tuple[str, str]]):
        for (name, club), n_edit, c_edit in zip(players, self.name_edits, self.club_edits):
            n_edit.setText(name)
            c_edit.setText(club)

    def lock(self):
        for edit in self.name_edits + self.club_edits:
            edit.setReadOnly(True)
        self.draw_btn.setEnabled(False)
        self.draw_btn.setText("Poules déjà tirées")
