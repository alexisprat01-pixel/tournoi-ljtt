"""Dialog to create or edit a tournament's metadata."""
from __future__ import annotations

from datetime import date

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QDateEdit, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox,
    QTextEdit, QVBoxLayout, QWidget, QCheckBox,
)

from ..models import Tournament


class TournamentDialog(QDialog):
    """Used for both 'new tournament' and 'edit tournament' flows."""

    def __init__(self, parent: QWidget | None = None, tournament: Tournament | None = None):
        super().__init__(parent)
        self._tournament = tournament
        self.setWindowTitle("Modifier le tournoi" if tournament else "Nouveau tournoi")
        self.setMinimumWidth(440)

        outer = QVBoxLayout(self)

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ex : Top12 — saison 2026")
        form.addRow("Nom du tournoi *", self.name_edit)

        # Date row with "no date" checkbox
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.no_date_check = QCheckBox("Pas de date définie")
        self.no_date_check.toggled.connect(lambda checked: self.date_edit.setDisabled(checked))

        form.addRow("Date de l'événement", self.date_edit)
        form.addRow("", self.no_date_check)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes libres (lieu, organisateur, observations…)")
        self.notes_edit.setMaximumHeight(120)
        form.addRow("Notes", self.notes_edit)

        outer.addLayout(form)

        if tournament is not None:
            self.name_edit.setText(tournament.name)
            if tournament.event_date:
                try:
                    y, m, d = (int(x) for x in tournament.event_date.split("-"))
                    self.date_edit.setDate(QDate(y, m, d))
                except (ValueError, AttributeError):
                    self.no_date_check.setChecked(True)
            else:
                self.no_date_check.setChecked(True)
            self.notes_edit.setPlainText(tournament.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Enregistrer" if tournament else "Créer"
        )
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _on_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Nom requis", "Le tournoi doit avoir un nom.")
            return
        self.accept()

    def get_values(self) -> tuple[str, str, str]:
        name = self.name_edit.text().strip()
        if self.no_date_check.isChecked():
            event_date = ""
        else:
            event_date = self.date_edit.date().toString("yyyy-MM-dd")
        notes = self.notes_edit.toPlainText().strip()
        return name, event_date, notes
