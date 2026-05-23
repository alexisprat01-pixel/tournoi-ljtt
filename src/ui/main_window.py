"""Main window — sidebar + stacked pages."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from ..database import Database
from ..models import Player
from ..tournament import (
    build_cross_rounds, build_pool_rounds, compute_standings, split_into_pools,
)
from .player_page import PlayerPage
from .rounds_page import RoundsPage
from .styles import STYLESHEET


def _assets_dir() -> Path:
    """Resolve the assets directory both in dev mode and inside a PyInstaller bundle."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "src" / "assets"
    return Path(__file__).resolve().parent.parent / "assets"


ASSETS_DIR = _assets_dir()


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("Top12 — Gestion de tournoi")
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._wire_nav()
        self._refresh_all()

    # ----- Build -----
    def _build_ui(self):
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo placeholder
        logo_label = QLabel()
        logo_label.setObjectName("sidebarLogo")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            logo_label.setPixmap(pix.scaledToWidth(180, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setText("⬤")
            logo_label.setStyleSheet("color:#C8102E; font-size:48pt; background-color:#1B1B1F; padding:16px;")
        sb_layout.addWidget(logo_label)

        title = QLabel("TOP 12")
        title.setObjectName("sidebarTitle")
        sb_layout.addWidget(title)

        subtitle = QLabel("Tennis de table")
        subtitle.setObjectName("sidebarSubtitle")
        sb_layout.addWidget(subtitle)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_players = self._nav_button("Joueurs", 0)
        self.btn_rounds = self._nav_button("Tours & matchs", 1)
        sb_layout.addWidget(self.btn_players)
        sb_layout.addWidget(self.btn_rounds)
        sb_layout.addStretch()

        self.reset_btn = QPushButton("Réinitialiser")
        self.reset_btn.setObjectName("secondary")
        self.reset_btn.clicked.connect(self._on_reset)
        sb_layout.addWidget(self.reset_btn)
        sb_layout.setContentsMargins(0, 0, 12, 12)

        layout.addWidget(sidebar)

        # Content stack
        self.stack = QStackedWidget()
        self.player_page = PlayerPage()
        self.rounds_page = RoundsPage()
        self.stack.addWidget(self.player_page)
        self.stack.addWidget(self.rounds_page)
        layout.addWidget(self.stack, 1)

        self.setCentralWidget(central)

        self.btn_players.setChecked(True)

    def _nav_button(self, label: str, page_index: int) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setProperty("page_index", page_index)
        self.nav_group.addButton(btn, page_index)
        return btn

    def _wire_nav(self):
        self.nav_group.idClicked.connect(self.stack.setCurrentIndex)
        self.player_page.pools_drawn.connect(self._on_pools_drawn)
        self.rounds_page.score_changed.connect(self._on_score_changed)
        self.rounds_page.generate_cross_requested.connect(self._on_generate_cross)

    # ----- Data flow -----
    def _refresh_all(self):
        players = self.db.list_players()
        matches = self.db.list_matches()

        if players:
            self.player_page.load_players([(p.name, p.club) for p in players])
            self.player_page.lock()
        self.rounds_page.set_data(players, matches)

        # Default page: rounds if already started
        if matches:
            self.stack.setCurrentIndex(1)
            self.btn_rounds.setChecked(True)
        else:
            self.stack.setCurrentIndex(0)
            self.btn_players.setChecked(True)

    def _on_pools_drawn(self, players_data: list[tuple[str, str]]):
        # Persist 12 players, split, build first 5 rounds
        self.db.reset_tournament()
        players: list[Player] = []
        for name, club in players_data:
            pid = self.db.insert_player(name, club)
            players.append(Player(id=pid, name=name, club=club))

        pool_a, pool_b = split_into_pools(players, shuffle=True)
        for p in pool_a + pool_b:
            self.db.update_player_pool(p.id, p.pool)

        matches = build_pool_rounds(pool_a, pool_b)
        self.db.insert_matches(matches)

        self.player_page.lock()
        self._refresh_all()
        self.stack.setCurrentIndex(1)
        self.btn_rounds.setChecked(True)

    def _on_score_changed(self, match_id: int, s1: int, s2: int, played: bool):
        self.db.update_match_score(match_id, s1, s2, played)
        self.rounds_page.set_data(self.db.list_players(), self.db.list_matches())

    def _on_generate_cross(self):
        players = self.db.list_players()
        matches = self.db.list_matches()

        # Verify pool phase complete
        pool_matches = [m for m in matches if m.phase == "pool"]
        if not pool_matches or not all(m.played for m in pool_matches):
            QMessageBox.warning(self, "Phase incomplète",
                                "Tous les matchs de poule doivent être joués pour générer la phase finale.")
            return

        # Already generated?
        if any(m.phase == "cross" for m in matches):
            confirm = QMessageBox.question(
                self, "Régénérer la phase finale",
                "La phase finale existe déjà. La régénérer effacera les scores des tours 6 à 11. Continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
            self.db.delete_matches_from_round(6)

        # Rank pools (max round 5)
        pool_a_ranked = [s.player for s in compute_standings(players, matches, pool="A", max_round=5)]
        pool_b_ranked = [s.player for s in compute_standings(players, matches, pool="B", max_round=5)]

        cross = build_cross_rounds(pool_a_ranked, pool_b_ranked)
        self.db.insert_matches(cross)
        self._refresh_all()

    def _on_reset(self):
        confirm = QMessageBox.question(
            self, "Réinitialiser le tournoi",
            "Cela effacera TOUS les joueurs et matchs enregistrés. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.db.reset_tournament()
        # Recreate UI from scratch
        self.player_page = PlayerPage()
        self.rounds_page = RoundsPage()
        # Replace pages in stack
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()
        self.stack.addWidget(self.player_page)
        self.stack.addWidget(self.rounds_page)
        self.player_page.pools_drawn.connect(self._on_pools_drawn)
        self.rounds_page.score_changed.connect(self._on_score_changed)
        self.rounds_page.generate_cross_requested.connect(self._on_generate_cross)
        self._refresh_all()
