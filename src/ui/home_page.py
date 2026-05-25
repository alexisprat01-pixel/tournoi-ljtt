"""Home page — list of saved tournaments + actions."""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget,
)

from ..database import Database
from ..models import Tournament
from .dialogs import confirm
from .styles import RED, TEXT
from .tournament_dialog import TournamentDialog


def _fmt_date(iso: str) -> str:
    if not iso:
        return "—"
    try:
        y, m, d = iso.split("-")
        return f"{d}/{m}/{y}"
    except ValueError:
        return iso


class HomePage(QWidget):
    """Tournament list with new/open/edit/delete actions."""

    open_requested = pyqtSignal(int)   # tournament_id

    def __init__(self, db: Database, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self._build()
        self.refresh()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 24, 32, 24)
        outer.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(
            f"<span style='color:{TEXT};'>Mes</span> "
            f"<span style='color:{RED};'>tournois</span>"
        )
        title.setObjectName("h1")
        header.addWidget(title)
        header.addStretch()
        new_btn = QPushButton("+ Nouveau tournoi")
        new_btn.clicked.connect(self._on_new)
        header.addWidget(new_btn)
        outer.addLayout(header)

        self.subtitle = QLabel("")
        self.subtitle.setObjectName("muted")
        outer.addWidget(self.subtitle)

        # List card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(4)
        self.list_widget.itemDoubleClicked.connect(self._on_open_selected)
        self.list_widget.setStyleSheet(
            "QListWidget { background-color: transparent; border: none; }"
            "QListWidget::item { background-color: #2A2A30; border-radius: 4px; padding: 4px; margin: 2px 0; }"
            "QListWidget::item:selected { background-color: #3A3A42; border-left: 4px solid #C8102E; }"
        )
        card_layout.addWidget(self.list_widget)

        # Actions row
        actions = QHBoxLayout()
        actions.addStretch()
        self.open_btn = QPushButton("Ouvrir")
        self.open_btn.clicked.connect(self._on_open_selected)
        self.edit_btn = QPushButton("Modifier")
        self.edit_btn.setObjectName("secondary")
        self.edit_btn.clicked.connect(self._on_edit_selected)
        self.delete_btn = QPushButton("Supprimer")
        self.delete_btn.setObjectName("secondary")
        self.delete_btn.clicked.connect(self._on_delete_selected)
        for b in (self.edit_btn, self.delete_btn, self.open_btn):
            actions.addWidget(b)
        card_layout.addLayout(actions)

        outer.addWidget(card, 1)

        self.empty_label = QLabel("Aucun tournoi enregistré. Clique sur \"+ Nouveau tournoi\" pour démarrer.")
        self.empty_label.setObjectName("muted")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self.empty_label)

        self.list_widget.itemSelectionChanged.connect(self._update_action_state)
        self._update_action_state()

    def refresh(self):
        tournaments = self.db.list_tournaments()
        self.list_widget.clear()
        for t in tournaments:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, t.id)
            widget = self._build_row(t)
            # Ask the widget how tall it wants to be once its labels are laid out,
            # then add a bit of breathing room.
            widget.adjustSize()
            hint_h = max(72, widget.sizeHint().height() + 12)
            item.setSizeHint(QSize(0, hint_h))
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        n = len(tournaments)
        self.subtitle.setText(
            "Aucun tournoi pour le moment." if n == 0
            else f"{n} tournoi{'s' if n > 1 else ''} enregistré{'s' if n > 1 else ''}."
        )
        self.empty_label.setVisible(n == 0)
        self.list_widget.setVisible(n > 0)
        self._update_action_state()

    def _build_row(self, t: Tournament) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background-color: transparent;")
        h = QHBoxLayout(row)
        h.setContentsMargins(16, 14, 16, 14)
        h.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(4)
        left.setContentsMargins(0, 0, 0, 0)

        name = QLabel(t.name)
        name.setStyleSheet("color: #F2F2F2; font-size: 12pt; font-weight: bold; background: transparent;")
        left.addWidget(name)

        # The 📅 character lives in the emoji block which Segoe UI does not cover.
        # Setting font families on the QLabel itself (rather than via inline HTML)
        # makes Qt fall back to Segoe UI Emoji for the emoji character only.
        meta = QLabel(
            f"📅  {_fmt_date(t.event_date)}    •    "
            f"Mis à jour le {_fmt_date(t.updated_at.split(' ')[0])}"
        )
        meta_font = QFont()
        meta_font.setFamilies(["Segoe UI", "Segoe UI Emoji", "Segoe UI Symbol"])
        meta_font.setPointSize(9)
        meta.setFont(meta_font)
        meta.setStyleSheet("color: #B4B4B8; background: transparent;")
        left.addWidget(meta)

        if t.notes:
            note_short = t.notes if len(t.notes) <= 90 else t.notes[:87] + "…"
            notes_label = QLabel(note_short)
            notes_label.setStyleSheet(
                "color: #B4B4B8; font-size: 9pt; font-style: italic; background: transparent;"
            )
            notes_label.setWordWrap(True)
            left.addWidget(notes_label)

        h.addLayout(left, 1)

        # Status pill
        players = self.db.list_players(t.id)
        matches = self.db.list_matches(t.id)
        status_text, status_color = self._status_for(players, matches)
        status = QLabel(status_text)
        status.setStyleSheet(
            f"background-color: {status_color}; color: white; padding: 6px 14px; "
            "border-radius: 11px; font-size: 9pt; font-weight: bold;"
        )
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setFixedHeight(28)
        h.addWidget(status, 0, Qt.AlignmentFlag.AlignVCenter)
        return row

    @staticmethod
    def _status_for(players, matches) -> tuple[str, str]:
        if not players:
            return "Brouillon", "#6c6c72"
        if not matches:
            return "Brouillon", "#6c6c72"
        if all(m.played for m in matches):
            return "Terminé", "#2e7d32"
        return "En cours", "#C8102E"

    def _update_action_state(self):
        has_sel = bool(self.list_widget.selectedItems())
        for b in (self.open_btn, self.edit_btn, self.delete_btn):
            b.setEnabled(has_sel)

    def _selected_id(self) -> int | None:
        items = self.list_widget.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.ItemDataRole.UserRole)

    # ----- Actions -----
    def _on_new(self):
        dlg = TournamentDialog(self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        name, event_date, notes, tournament_type = dlg.get_values()
        t = self.db.create_tournament(name, event_date, notes, tournament_type)
        self.refresh()
        self.open_requested.emit(t.id)

    def _on_open_selected(self):
        tid = self._selected_id()
        if tid is None:
            return
        self.open_requested.emit(tid)

    def _on_edit_selected(self):
        tid = self._selected_id()
        if tid is None:
            return
        t = self.db.get_tournament(tid)
        if t is None:
            return
        dlg = TournamentDialog(self, tournament=t)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        name, event_date, notes, tournament_type = dlg.get_values()
        self.db.update_tournament(tid, name, event_date, notes, tournament_type)
        self.refresh()

    def _on_delete_selected(self):
        tid = self._selected_id()
        if tid is None:
            return
        t = self.db.get_tournament(tid)
        if t is None:
            return
        if not confirm(
            self, "Supprimer le tournoi",
            f"Supprimer définitivement « {t.name} » et toutes ses données (joueurs, matchs) ?",
            default_yes=False,
        ):
            return
        self.db.delete_tournament(tid)
        self.refresh()
