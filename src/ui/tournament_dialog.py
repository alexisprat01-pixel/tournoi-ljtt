"""Dialog to create or edit a tournament's metadata."""
from __future__ import annotations

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QCheckBox, QDateEdit, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from ..models import Tournament
from .styles import RED, TEXT, TEXT_DIM


class TournamentDialog(QDialog):
    """Used for both 'new tournament' and 'edit tournament' flows."""

    def __init__(self, parent: QWidget | None = None, tournament: Tournament | None = None):
        super().__init__(parent)
        self._tournament = tournament
        self.setWindowTitle("Modifier le tournoi" if tournament else "Nouveau tournoi")
        self.setMinimumWidth(480)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(16)

        # Bicolor title — consistent with the rest of the app
        if tournament:
            title_html = (
                f"<span style='color:{TEXT};'>Modifier le</span> "
                f"<span style='color:{RED};'>tournoi</span>"
            )
            subtitle_text = "Ajuste le nom, la date ou les notes du tournoi en cours."
            primary_text = "Enregistrer"
        else:
            title_html = (
                f"<span style='color:{TEXT};'>Nouveau</span> "
                f"<span style='color:{RED};'>tournoi</span>"
            )
            subtitle_text = "Renseigne les infos générales — tu pourras les modifier ensuite."
            primary_text = "Créer"

        title = QLabel(title_html)
        title.setStyleSheet(
            "font-size: 20pt; font-weight: bold; background: transparent;"
        )
        outer.addWidget(title)

        subtitle = QLabel(subtitle_text)
        subtitle.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.setContentsMargins(0, 6, 0, 6)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ex : Top12 — saison 2026")
        form.addRow(self._field_label("Nom du tournoi *"), self.name_edit)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setDate(QDate.currentDate())
        self.no_date_check = QCheckBox("Pas de date définie")
        self.no_date_check.toggled.connect(lambda checked: self.date_edit.setDisabled(checked))

        form.addRow(self._field_label("Date de l'événement"), self.date_edit)
        form.addRow("", self.no_date_check)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes libres (lieu, organisateur, observations…)")
        self.notes_edit.setMaximumHeight(120)
        form.addRow(self._field_label("Notes"), self.notes_edit)

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

        # Buttons row — pill style via QSS
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        primary_btn = QPushButton(primary_text)
        primary_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(primary_btn)
        outer.addLayout(btn_row)

    @staticmethod
    def _field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {RED}; font-weight: bold; font-size: 9pt; "
            "background: transparent; letter-spacing: 1px;"
        )
        return lbl

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
