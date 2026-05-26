"""Rounds page — horizontal tab bar selects a single round; pool standings stay below."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QPainterPath, QRegion
from PyQt6.QtWidgets import (
    QAbstractScrollArea, QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..models import Match, Player, PlayerStanding
from ..tournament import compute_standings
from .match_card import MatchCard
from .print_export import open_match_print_preview
from .styles import GREY, GREY_DARK, GREY_LIGHT, RED, TEXT, TEXT_DIM
from .widgets import make_page_header


class RoundsPage(QWidget):
    """One round at a time (selected via tabs) + pool standings always visible.

    session=1 → pool phase (rounds 1-5), shows the "generate finals" action button.
    session=2 → cross phase (rounds 6-11).
    Pool standings are rendered at the bottom in both sessions.
    """

    sets_saved = pyqtSignal(int, list)
    generate_cross_requested = pyqtSignal()

    def __init__(self, session: int = 1, parent: QWidget | None = None):
        super().__init__(parent)
        self.session = session
        self._players: dict[int, Player] = {}
        self._matches: list[Match] = []
        self._selected_round: int | None = None
        self._build()

    # ----- Layout skeleton -----
    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setContentsMargins(32, 24, 32, 0)
        self._header_holder = QWidget()
        self._header_layout = QVBoxLayout(self._header_holder)
        self._header_layout.setContentsMargins(0, 0, 0, 0)
        self._header_layout.setSpacing(0)
        header.addWidget(self._header_holder, 1)
        # Primary red button — same prominence as "Générer la phase finale".
        self.print_btn = QPushButton("🖨  Imprimer les matchs")
        self.print_btn.setVisible(False)
        self.print_btn.clicked.connect(self._on_print_clicked)
        header.addWidget(self.print_btn, 0, Qt.AlignmentFlag.AlignTop)

        self.action_btn = QPushButton("Générer la phase finale")
        self.action_btn.setVisible(False)
        self.action_btn.clicked.connect(self.generate_cross_requested.emit)
        header.addWidget(self.action_btn, 0, Qt.AlignmentFlag.AlignTop)
        outer.addLayout(header)
        # Initial placeholder so the layout has a non-zero header height
        self._set_header(self.session, "Phase de poules" if self.session == 1 else "Phase finale",
                         accent_word="poules" if self.session == 1 else "finale")

        self.subtitle = QLabel("")
        self.subtitle.setObjectName("muted")
        self.subtitle.setContentsMargins(32, 0, 32, 0)
        self.subtitle.setWordWrap(True)
        outer.addWidget(self.subtitle)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(32, 16, 32, 24)
        self.content_layout.setSpacing(12)
        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll, 1)

    # ----- Public API -----
    def set_data(self, players: list[Player], matches: list[Match]):
        self._players = {p.id: p for p in players}
        self._matches = matches
        # Default selected round = first one available in this session.
        rounds = self._available_rounds()
        if rounds and self._selected_round not in rounds:
            self._selected_round = rounds[0]
        elif not rounds:
            self._selected_round = None
        self._render()

    # ----- Internals -----
    def _available_rounds(self) -> list[int]:
        target_phase = "pool" if self.session == 1 else "cross"
        return sorted({m.round_number for m in self._matches if m.phase == target_phase})

    def _on_tab_clicked(self, round_num: int):
        self._selected_round = round_num
        self._render()

    def _on_print_clicked(self):
        target_phase = "pool" if self.session == 1 else "cross"
        session_matches = [m for m in self._matches if m.phase == target_phase]
        open_match_print_preview(
            self, session_matches, list(self._players.values()), self.session,
        )

    def _clear_layout(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _render(self):
        self._clear_layout()
        self._render_header()
        rounds = self._available_rounds()
        if rounds:
            self.content_layout.addWidget(self._build_tab_bar(rounds))
            if self._selected_round in rounds:
                self.content_layout.addWidget(self._build_round_card(self._selected_round))
        # Bottom standings: pool side-by-side in Session 1, overall ranking in Session 2.
        bottom = self._build_bottom_standings()
        if bottom is not None:
            self.content_layout.addWidget(bottom)
        self.content_layout.addStretch()

    def _render_header(self):
        pool_rounds = [m for m in self._matches if m.phase == "pool"]
        cross_rounds = [m for m in self._matches if m.phase == "cross"]
        pools_complete = bool(pool_rounds) and all(m.played for m in pool_rounds)

        # Print button is visible whenever there is something to print in this session.
        target_phase = "pool" if self.session == 1 else "cross"
        has_session_matches = any(m.phase == target_phase for m in self._matches)
        self.print_btn.setVisible(has_session_matches)

        if self.session == 1:
            if not pool_rounds:
                self._set_header(1, "Phase de poules", accent_word="poules")
                self.subtitle.setText(
                    "Les poules ne sont pas encore tirées. "
                    "Va dans l'onglet \"Joueurs\" pour démarrer."
                )
                self.action_btn.setVisible(False)
                return
            if pools_complete and not cross_rounds:
                self._set_header(1, "Phase terminée", accent_word="terminée")
                self.subtitle.setText(
                    "Tous les matchs de poule sont joués. "
                    "Tu peux générer la Session 2 (phase finale)."
                )
                self.action_btn.setText("Générer la phase finale")
                self.action_btn.setVisible(True)
            elif cross_rounds:
                self._set_header(1, "Phase de poules", accent_word="poules")
                self.subtitle.setText("La Session 2 (phase finale) est déjà générée.")
                self.action_btn.setVisible(False)
            else:
                self._set_header(1, "Phase de poules", accent_word="poules")
                self.subtitle.setText(
                    "Tours 1 à 5 — chaque joueur rencontre les 5 autres de sa poule."
                )
                self.action_btn.setVisible(False)
        else:
            # Session 2
            if not cross_rounds:
                self._set_header(2, "Phase finale", accent_word="finale")
                self.subtitle.setText(
                    "La phase finale n'est pas encore générée. Termine la Session 1 "
                    "et clique sur \"Générer la phase finale\"."
                )
                self.action_btn.setVisible(False)
                return
            self._set_header(2, "Phase finale", accent_word="finale")
            self.subtitle.setText(
                "Tours 6 à 11 — chaque joueur de la poule A affronte tous ceux de la "
                "poule B. Le tour 11 oppose les joueurs de même rang."
            )
            self.action_btn.setVisible(False)

    def _set_header(self, session_no: int, title: str, *, accent_word: str | None) -> None:
        """Rebuild the editorial header (eyebrow + title + rule) for this state."""
        while self._header_layout.count():
            item = self._header_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        eyebrow = f"Session {session_no}"
        self._header_layout.addWidget(
            make_page_header(title, eyebrow=eyebrow, accent_word=accent_word)
        )

    # ----- Tab bar -----
    def _build_tab_bar(self, rounds: list[int]) -> QFrame:
        bar = QFrame()
        bar.setStyleSheet(f"background-color:{GREY_DARK}; border-radius:6px;")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(6, 6, 6, 6)
        bl.setSpacing(4)
        for r in rounds:
            active = (r == self._selected_round)
            btn = QPushButton(f"Tour {r}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if active:
                btn.setStyleSheet(
                    f"background-color:{RED}; color:white; font-weight:bold; "
                    "padding:8px 16px; border-radius:4px; border:none;"
                )
            else:
                btn.setStyleSheet(
                    f"background-color:transparent; color:{TEXT_DIM}; "
                    "padding:8px 16px; border-radius:4px; border:none;"
                )
            btn.clicked.connect(lambda _checked=False, r=r: self._on_tab_clicked(r))
            bl.addWidget(btn)
        bl.addStretch()
        return bar

    # ----- Selected round content -----
    def _build_round_card(self, round_num: int) -> QFrame:
        round_matches = [
            m for m in self._matches
            if m.round_number == round_num
            and m.phase == ("pool" if self.session == 1 else "cross")
        ]

        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 14)
        cl.setSpacing(8)

        # Header row: title + "X / N joués" badge
        head = QHBoxLayout()
        head.setSpacing(8)
        title_text = f"Tour {round_num}"
        if round_num == 11:
            title_text += "  —  finale par rang"
        head_title = QLabel(title_text)
        head_title.setStyleSheet(
            f"color:{TEXT}; font-size:14pt; font-weight:bold; background:transparent;"
        )
        head.addWidget(head_title)
        head.addStretch()
        played = sum(1 for m in round_matches if m.played)
        status = QLabel(f"{played} / {len(round_matches)} joués")
        status.setStyleSheet(
            f"color:{TEXT_DIM}; font-size:9pt; background:transparent;"
        )
        head.addWidget(status)
        head_w = QWidget()
        head_w.setLayout(head)
        head_w.setStyleSheet("background:transparent;")
        cl.addWidget(head_w)

        # Matches
        if self.session == 1:
            for pool in ("A", "B"):
                pool_matches = [m for m in round_matches if m.pool == pool]
                if pool_matches:
                    sub = QLabel(f"Poule {pool}")
                    sub.setStyleSheet(
                        f"color:{TEXT_DIM}; font-weight:bold; padding-top:4px; "
                        "background:transparent;"
                    )
                    cl.addWidget(sub)
                    for m in pool_matches:
                        cl.addWidget(self._make_match_card(m))
        else:
            for m in round_matches:
                cl.addWidget(self._make_match_card(m))

        return card

    def _make_match_card(self, m: Match) -> QWidget:
        p1 = self._players.get(m.player1_id)
        p2 = self._players.get(m.player2_id)
        if p1 is None or p2 is None:
            placeholder = QLabel("Match invalide")
            return placeholder
        referee = self._players.get(m.referee_id) if m.referee_id else None
        card = MatchCard(m, p1, p2, referee=referee)
        card.sets_saved.connect(self.sets_saved.emit)
        return card

    # ----- Bottom standings (pool side-by-side OR overall) -----
    def _build_bottom_standings(self) -> QWidget | None:
        if self.session == 2:
            return self._build_general_standings()
        if not any(m.phase == "pool" for m in self._matches):
            return None
        return self._build_pool_standings()

    def _build_general_standings(self) -> QWidget | None:
        if not self._matches:
            return None
        wrapper = QWidget()
        v = QVBoxLayout(wrapper)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(8)
        header = QLabel("Classement général")
        header.setObjectName("h2")
        v.addWidget(header)
        standings = compute_standings(self._players.values(), self._matches)
        v.addWidget(self._wrap_table(self._standings_table(standings)))
        return wrapper

    # ----- Pool standings (Session 1) -----
    def _build_pool_standings(self) -> QWidget:
        wrapper = QWidget()
        v = QVBoxLayout(wrapper)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(8)

        header = QLabel("Classement des poules")
        header.setObjectName("h2")
        v.addWidget(header)

        row = QHBoxLayout()
        for pool in ("A", "B"):
            box = QVBoxLayout()
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(8)
            lbl = QLabel(f"Poule {pool}")
            lbl.setObjectName("h2")
            box.addWidget(lbl)
            box.addWidget(self._wrap_table(self._standings_table(
                compute_standings(
                    self._players.values(),
                    self._matches,
                    pool=pool,
                    max_round=5,
                )
            )))
            box.addStretch(1)  # keep both columns aligned to the top
            cnt = QWidget()
            cnt.setLayout(box)
            row.addWidget(cnt)
        row.setAlignment(Qt.AlignmentFlag.AlignTop)
        row_w = QWidget()
        row_w.setLayout(row)
        v.addWidget(row_w)
        return wrapper

    @staticmethod
    def _wrap_table(table: QTableWidget) -> QFrame:
        """Wrap a table inside a rounded QFrame *with a real rounded mask*.

        QSS border-radius doesn't clip child widgets — the table viewport
        keeps painting over the corners. Setting a QRegion mask actually
        constrains the rendered area to the rounded shape, so all four
        corners look round, including the bottom ones."""

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
    def _standings_table(standings: list[PlayerStanding]) -> QTableWidget:
        table = QTableWidget(len(standings), 6)
        table.setHorizontalHeaderLabels(["#", "Joueur", "J", "V", "Pts", "Diff sets"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # Bigger, semi-bold name column to match the general standings page.
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
        # Make the viewport transparent so the rounded wrap frame shows through.
        table.viewport().setAutoFillBackground(False)
        table.viewport().setStyleSheet("background: transparent;")
        table.setFrameShape(QFrame.Shape.NoFrame)
        # Deterministic row height based on the (largest) font used in rows.
        # Same value for every standings table, so pools A and B align perfectly.
        fm = QFontMetrics(name_font)
        row_h = fm.height() + 14  # vertical padding around the text
        vh = table.verticalHeader()
        vh.setDefaultSectionSize(row_h)
        vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        # Header height: take a generous max between sizeHint and font-derived,
        # so QSS padding never pushes content into row 1.
        header_fm = QFontMetrics(table.font())
        header_h = max(header.sizeHint().height(), header_fm.height() + 18)
        header.setFixedHeight(header_h)
        table.setFixedHeight(
            header_h + row_h * table.rowCount() + 2 * table.frameWidth()
        )
        return table
