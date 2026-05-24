"""Main window — home page + per-tournament workspace."""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from ..database import Database
from ..models import Player, Tournament
from ..tournament import (
    assign_tables_and_referees, build_cross_rounds, build_pool_rounds,
    collect_assignment_counts, compute_standings, derive_match_result,
    group_matches_into_sessions, split_into_pools,
)
from .dialogs import confirm
from .general_ranking_page import GeneralRankingPage
from .home_page import HomePage
from .player_page import PlayerPage
from .rounds_page import RoundsPage
from .statistics_page import StatisticsPage
from .styles import (
    BLACK, GREY, GREY_DARK, GREY_LIGHT, RED, STYLESHEET, TEXT, TEXT_DIM,
    GlowBackground,
)
from .tournament_dialog import TournamentDialog


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
        self._current_tournament: Tournament | None = None
        self._player_page: PlayerPage | None = None
        self._session1_page: RoundsPage | None = None
        self._session2_page: RoundsPage | None = None
        self._general_page: GeneralRankingPage | None = None
        self._stats_page: StatisticsPage | None = None

        self.setWindowTitle("Top12 — Gestion de tournoi")
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._show_home()

    # ----- Layout -----
    def _build_ui(self):
        # Custom-painted widget that draws the bg + radial red glow.
        central = GlowBackground()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ===== Sidebar =====
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)

        # --- Logo strip (compact: logo + brand on one row) ---
        strip = QFrame()
        strip.setStyleSheet(f"background-color:{GREY_DARK};")
        sv = QHBoxLayout(strip)
        sv.setContentsMargins(14, 10, 14, 10)
        sv.setSpacing(10)
        logo_label = QLabel()
        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            logo_label.setPixmap(pix.scaledToWidth(32, Qt.TransformationMode.SmoothTransformation))
            logo_label.setStyleSheet("background:transparent;")
        else:
            logo_label.setText("⬤")
            logo_label.setStyleSheet(f"color:{RED}; font-size:18pt; background:transparent;")
        sv.addWidget(logo_label)
        brand = QLabel("TOP 12")
        brand.setStyleSheet(f"color:{RED}; font-size:13pt; font-weight:bold; background:transparent;")
        sv.addWidget(brand)
        sv.addStretch()
        sb.addWidget(strip)
        sb.addWidget(self._hline())

        # --- Section TOURNOI (hidden on home) ---
        self.tournament_section = QWidget()
        ts = QVBoxLayout(self.tournament_section)
        ts.setContentsMargins(14, 12, 14, 12)
        ts.setSpacing(2)
        ts.addWidget(self._section_header("TOURNOI"))
        self.tournament_name_lbl = QLabel("")
        self.tournament_name_lbl.setStyleSheet(
            f"color:{TEXT}; font-size:11pt; font-weight:bold; background:transparent;"
        )
        self.tournament_name_lbl.setWordWrap(True)
        ts.addWidget(self.tournament_name_lbl)
        self.tournament_meta_lbl = QLabel("")
        self.tournament_meta_lbl.setStyleSheet(
            f"color:{TEXT_DIM}; font-size:9pt; background:transparent;"
        )
        self.tournament_meta_lbl.setWordWrap(True)
        ts.addWidget(self.tournament_meta_lbl)
        sb.addWidget(self.tournament_section)
        self._tournament_hr = self._hline()
        sb.addWidget(self._tournament_hr)

        # --- Section NAVIGATION ---
        self.nav_section = QWidget()
        ns = QVBoxLayout(self.nav_section)
        ns.setContentsMargins(0, 10, 0, 10)
        ns.setSpacing(2)
        nav_head = self._section_header("NAVIGATION")
        nav_head.setContentsMargins(14, 0, 14, 4)
        ns.addWidget(nav_head)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.btn_players = self._nav_button("Joueurs", 1)
        self.btn_session1 = self._nav_button("Session 1", 2)
        self.btn_session2 = self._nav_button("Session 2", 3)
        self.btn_general = self._nav_button("Classement général", 4)
        self.btn_stats = self._nav_button("Statistiques", 5)
        ns.addWidget(self.btn_players)
        ns.addWidget(self.btn_session1)
        ns.addWidget(self.btn_session2)
        ns.addWidget(self.btn_general)
        ns.addWidget(self.btn_stats)
        sb.addWidget(self.nav_section)
        self._nav_hr = self._hline()
        sb.addWidget(self._nav_hr)

        sb.addStretch()

        # --- Section ACTIONS ---
        self.actions_section = QWidget()
        ac = QVBoxLayout(self.actions_section)
        ac.setContentsMargins(14, 10, 14, 12)
        ac.setSpacing(4)
        ac.addWidget(self._section_header("ACTIONS"))

        self.edit_meta_btn = QPushButton("Modifier les infos")
        self.edit_meta_btn.setObjectName("secondary")
        self.edit_meta_btn.clicked.connect(self._on_edit_meta)
        ac.addWidget(self.edit_meta_btn)

        self.reset_btn = QPushButton("Vider ce tournoi")
        self.reset_btn.setObjectName("secondary")
        self.reset_btn.clicked.connect(self._on_reset_current)
        ac.addWidget(self.reset_btn)

        self.home_btn = QPushButton("← Mes tournois")
        self.home_btn.setObjectName("secondary")
        self.home_btn.clicked.connect(self._show_home)
        ac.addWidget(self.home_btn)

        sb.addWidget(self.actions_section)

        layout.addWidget(self.sidebar)

        # ===== Stack =====
        self.stack = QStackedWidget()
        self.home_page = HomePage(self.db)
        self.home_page.open_requested.connect(self._open_tournament)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(QWidget())  # placeholder players  (1)
        self.stack.addWidget(QWidget())  # placeholder session1 (2)
        self.stack.addWidget(QWidget())  # placeholder session2 (3)
        self.stack.addWidget(QWidget())  # placeholder general  (4)
        self.stack.addWidget(QWidget())  # placeholder stats    (5)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.nav_group.idClicked.connect(self.stack.setCurrentIndex)

    @staticmethod
    def _hline() -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.HLine)
        f.setStyleSheet(
            f"color:{GREY_LIGHT}; background-color:{GREY_LIGHT}; max-height:1px; min-height:1px;"
        )
        return f

    @staticmethod
    def _section_header(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{TEXT_DIM}; font-size:8pt; font-weight:bold; "
            "background:transparent; letter-spacing:1px;"
        )
        return lbl

    def _nav_button(self, label: str, page_index: int) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setProperty("page_index", page_index)
        self.nav_group.addButton(btn, page_index)
        return btn

    def _set_tournament_sidebar_visible(self, visible: bool):
        for w in (
            self.tournament_section,
            self._tournament_hr,
            self.nav_section,
            self._nav_hr,
            self.actions_section,
        ):
            w.setVisible(visible)

    # ----- Navigation -----
    def _show_home(self):
        self._current_tournament = None
        self.home_page.refresh()
        self._set_tournament_sidebar_visible(False)
        self.stack.setCurrentIndex(0)
        self.setWindowTitle("Top12 — Gestion de tournoi")

    def _open_tournament(self, tournament_id: int):
        t = self.db.get_tournament(tournament_id)
        if t is None:
            QMessageBox.warning(self, "Tournoi introuvable", "Ce tournoi n'existe plus.")
            self._show_home()
            return
        self._current_tournament = t
        self._backfill_assignments_if_needed(t.id)
        self._mount_tournament_pages()
        self._update_context_label()
        self._set_tournament_sidebar_visible(True)

        # Default page depending on tournament state
        matches = self.db.list_matches(t.id)
        if matches:
            self.btn_session1.setChecked(True)
            self.stack.setCurrentIndex(2)
        else:
            self.btn_players.setChecked(True)
            self.stack.setCurrentIndex(1)

        self.setWindowTitle(f"Top12 — {t.name}")

    def _backfill_assignments_if_needed(self, tournament_id: int):
        """Fix table/referee assignments when they are missing OR violate the per-session
        'tables must be {1, 2, 3}' constraint.

        Table and referee assignments are an algorithmic property of the tournament, not
        a record of physical reality (no one keys it in by hand). So when the algorithm
        produced a broken layout — typically because the tournament was created before
        the session-aware version landed — we reset *every* match's table/referee, played
        or not, and rerun the algorithm from scratch. Scores, sets, and the played flag
        are preserved.
        """
        matches = self.db.list_matches(tournament_id)
        if not matches:
            return
        players = self.db.list_players(tournament_id)
        if len(players) < 3:
            return

        needs_fix = False
        for session in group_matches_into_sessions(matches):
            if any(m.table_number == 0 or m.referee_id == 0 for m in session):
                needs_fix = True
                break
            tables = [m.table_number for m in session]
            if len(set(tables)) != len(tables):
                needs_fix = True
                break
            refs = [m.referee_id for m in session if m.referee_id]
            if len(set(refs)) != len(refs):
                needs_fix = True
                break
        if not needs_fix:
            return

        # Reset ALL matches' table & referee (scores preserved).
        for m in matches:
            if m.table_number or m.referee_id:
                self.db.update_match_assignment(m.id, 0, 0)

        # Reload after the reset, then recompute from a clean slate.
        matches = self.db.list_matches(tournament_id)
        player_ids = [p.id for p in players]
        assign_tables_and_referees(matches, player_ids)
        for m in matches:
            self.db.update_match_assignment(m.id, m.table_number, m.referee_id)

    def _update_context_label(self):
        if self._current_tournament is None:
            return
        t = self._current_tournament
        self.tournament_name_lbl.setText(t.name)
        date_str = self._fmt_iso_date(t.event_date)
        status = self._compute_status(t.id)
        self.tournament_meta_lbl.setText(f"{date_str}  ·  {status}")

    @staticmethod
    def _fmt_iso_date(iso: str) -> str:
        if not iso:
            return "Pas de date"
        try:
            y, m, d = iso.split("-")
            return f"{d}/{m}/{y}"
        except ValueError:
            return iso

    def _compute_status(self, tournament_id: int) -> str:
        players = self.db.list_players(tournament_id)
        matches = self.db.list_matches(tournament_id)
        if not players or not matches:
            return "Brouillon"
        if all(m.played for m in matches):
            return "Terminé"
        return "En cours"

    def _mount_tournament_pages(self):
        """Build fresh pages for the current tournament (players + 2 sessions + general)."""
        assert self._current_tournament is not None
        t = self._current_tournament

        # Replace placeholders at indexes 1..5 (reverse order to keep indexes stable).
        for idx in (5, 4, 3, 2, 1):
            w = self.stack.widget(idx)
            self.stack.removeWidget(w)
            w.deleteLater()

        self._player_page = PlayerPage()
        self._player_page.pools_drawn.connect(self._on_pools_drawn)
        self.stack.insertWidget(1, self._player_page)

        self._session1_page = RoundsPage(session=1)
        self._session1_page.sets_saved.connect(self._on_sets_saved)
        self._session1_page.generate_cross_requested.connect(self._on_generate_cross)
        self.stack.insertWidget(2, self._session1_page)

        self._session2_page = RoundsPage(session=2)
        self._session2_page.sets_saved.connect(self._on_sets_saved)
        self.stack.insertWidget(3, self._session2_page)

        self._general_page = GeneralRankingPage()
        self.stack.insertWidget(4, self._general_page)

        self._stats_page = StatisticsPage()
        self.stack.insertWidget(5, self._stats_page)

        players = self.db.list_players(t.id)
        matches = self.db.list_matches(t.id)
        if players:
            self._player_page.load_players([(p.name, p.points) for p in players])
        self._player_page.set_state(
            has_pools=bool(matches),
            has_played_matches=any(m.played for m in matches),
        )
        self._session1_page.set_data(players, matches)
        self._session2_page.set_data(players, matches)
        self._general_page.set_data(players, matches)
        self._stats_page.set_data(players, matches)

    # ----- Tournament actions -----
    def _on_pools_drawn(self, players_data: list[tuple[str, int]]):
        assert self._current_tournament is not None
        tid = self._current_tournament.id
        # Wipe any pre-existing data on this tournament (defensive)
        self.db.reset_tournament_data(tid)
        players: list[Player] = []
        for name, points in players_data:
            pid = self.db.insert_player(tid, name, points)
            players.append(Player(id=pid, name=name, points=points))

        pool_a, pool_b = split_into_pools(players)
        for p in pool_a + pool_b:
            self.db.update_player_pool(p.id, p.pool)

        matches = build_pool_rounds(pool_a, pool_b)
        player_ids = [p.id for p in players]
        assign_tables_and_referees(matches, player_ids)
        self.db.insert_matches(tid, matches)

        # Refresh local pages
        all_players = self.db.list_players(tid)
        all_matches = self.db.list_matches(tid)
        if self._player_page:
            self._player_page.set_state(
                has_pools=bool(all_matches),
                has_played_matches=any(m.played for m in all_matches),
            )
        if self._session1_page:
            self._session1_page.set_data(all_players, all_matches)
        if self._session2_page:
            self._session2_page.set_data(all_players, all_matches)
        if self._general_page:
            self._general_page.set_data(all_players, all_matches)
        if self._stats_page:
            self._stats_page.set_data(all_players, all_matches)
        self.btn_session1.setChecked(True)
        self.stack.setCurrentIndex(2)
        self._update_context_label()

    def _on_sets_saved(self, match_id: int, set_scores: list):
        if self._current_tournament is None:
            return
        s1, s2, played = derive_match_result(set_scores)
        self.db.update_match_sets(match_id, set_scores, s1, s2, played)
        tid = self._current_tournament.id
        players = self.db.list_players(tid)
        matches = self.db.list_matches(tid)
        if self._session1_page is not None:
            self._session1_page.set_data(players, matches)
        if self._session2_page is not None:
            self._session2_page.set_data(players, matches)
        if self._general_page is not None:
            self._general_page.set_data(players, matches)
        if self._stats_page is not None:
            self._stats_page.set_data(players, matches)
        # As soon as one score is recorded, the player list is locked.
        if self._player_page is not None:
            self._player_page.set_state(
                has_pools=bool(matches),
                has_played_matches=any(m.played for m in matches),
            )
        # Refresh the sidebar status (Brouillon → En cours → Terminé).
        self._update_context_label()

    def _on_generate_cross(self):
        if self._current_tournament is None:
            return
        tid = self._current_tournament.id
        players = self.db.list_players(tid)
        matches = self.db.list_matches(tid)

        pool_matches = [m for m in matches if m.phase == "pool"]
        if not pool_matches or not all(m.played for m in pool_matches):
            QMessageBox.warning(self, "Phase incomplète",
                                "Tous les matchs de poule doivent être joués pour générer la phase finale.")
            return

        if any(m.phase == "cross" for m in matches):
            if not confirm(
                self, "Régénérer la phase finale",
                "La phase finale existe déjà. La régénérer effacera les scores des tours 6 à 11, "
                "et recalculera aussi les tables / arbitres des matchs de poule "
                "(les scores des poules sont préservés). Continuer ?",
                default_yes=False,
            ):
                return
            self.db.delete_matches_from_round(tid, 6)

        pool_a_ranked = [s.player for s in compute_standings(players, matches, pool="A", max_round=5)]
        pool_b_ranked = [s.player for s in compute_standings(players, matches, pool="B", max_round=5)]

        cross = build_cross_rounds(pool_a_ranked, pool_b_ranked)
        self.db.insert_matches(tid, cross)

        # Co-optimise table & referee assignments across the whole tournament:
        # reset everything in memory, run the algo on the full match list, then persist.
        # Scores / played flag are stored separately and are untouched.
        all_matches = self.db.list_matches(tid)
        for m in all_matches:
            m.table_number = 0
            m.referee_id = 0
        player_ids = [p.id for p in players]
        assign_tables_and_referees(all_matches, player_ids)
        for m in all_matches:
            self.db.update_match_assignment(m.id, m.table_number, m.referee_id)
        all_players = self.db.list_players(tid)
        all_matches = self.db.list_matches(tid)
        if self._session1_page:
            self._session1_page.set_data(all_players, all_matches)
        if self._session2_page:
            self._session2_page.set_data(all_players, all_matches)
        if self._general_page:
            self._general_page.set_data(all_players, all_matches)
        if self._stats_page:
            self._stats_page.set_data(all_players, all_matches)
        # Jump straight to Session 2 so the user can see the freshly generated matches.
        self.btn_session2.setChecked(True)
        self.stack.setCurrentIndex(3)
        self._update_context_label()

    def _on_edit_meta(self):
        if self._current_tournament is None:
            return
        dlg = TournamentDialog(self, tournament=self._current_tournament)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        name, event_date, notes = dlg.get_values()
        self.db.update_tournament(self._current_tournament.id, name, event_date, notes)
        self._current_tournament = self.db.get_tournament(self._current_tournament.id)
        self._update_context_label()
        self.setWindowTitle(f"Top12 — {self._current_tournament.name}")
        self.home_page.refresh()

    def _on_reset_current(self):
        if self._current_tournament is None:
            return
        if not confirm(
            self, "Vider le tournoi",
            f"Effacer les joueurs et matchs de « {self._current_tournament.name} » ? "
            "Les infos du tournoi (nom, date, notes) sont conservées.",
            default_yes=False,
        ):
            return
        self.db.reset_tournament_data(self._current_tournament.id)
        self._mount_tournament_pages()
        self.btn_players.setChecked(True)
        self.stack.setCurrentIndex(1)
