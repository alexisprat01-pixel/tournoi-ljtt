"""Rounds page — horizontal tab bar selects a single round; pool standings stay below."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton, QScrollArea,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..models import Match, Player, PlayerStanding
from ..tournament import compute_standings
from .match_card import MatchCard
from .styles import GREY, GREY_DARK, GREY_LIGHT, RED, TEXT, TEXT_DIM


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
        self.title = QLabel("")
        self.title.setObjectName("h1")
        header.addWidget(self.title)
        header.addStretch()
        self.action_btn = QPushButton("Générer la phase finale")
        self.action_btn.setVisible(False)
        self.action_btn.clicked.connect(self.generate_cross_requested.emit)
        header.addWidget(self.action_btn)
        outer.addLayout(header)

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

        # Editorial bicolor title: white prefix + red phase.
        prefix_white = f"<span style='color:{TEXT};'>"
        prefix_red = f"<span style='color:{RED};'>"
        end = "</span>"

        if self.session == 1:
            if not pool_rounds:
                self.title.setText(f"{prefix_white}Session 1{end} {prefix_red}Phase de poules{end}")
                self.subtitle.setText(
                    "Les poules ne sont pas encore tirées. "
                    "Va dans l'onglet \"Joueurs\" pour démarrer."
                )
                self.action_btn.setVisible(False)
                return
            if pools_complete and not cross_rounds:
                self.title.setText(f"{prefix_white}Session 1{end} {prefix_red}Phase terminée{end}")
                self.subtitle.setText(
                    "Tous les matchs de poule sont joués. "
                    "Tu peux générer la Session 2 (phase finale)."
                )
                self.action_btn.setText("Générer la phase finale")
                self.action_btn.setVisible(True)
            elif cross_rounds:
                self.title.setText(f"{prefix_white}Session 1{end} {prefix_red}Phase de poules{end}")
                self.subtitle.setText("La Session 2 (phase finale) est déjà générée.")
                self.action_btn.setVisible(False)
            else:
                self.title.setText(f"{prefix_white}Session 1{end} {prefix_red}Phase de poules{end}")
                self.subtitle.setText(
                    "Tours 1 à 5 — chaque joueur rencontre les 5 autres de sa poule."
                )
                self.action_btn.setVisible(False)
        else:
            # Session 2
            if not cross_rounds:
                self.title.setText(f"{prefix_white}Session 2{end} {prefix_red}Phase finale{end}")
                self.subtitle.setText(
                    "La phase finale n'est pas encore générée. Termine la Session 1 "
                    "et clique sur \"Générer la phase finale\"."
                )
                self.action_btn.setVisible(False)
                return
            self.title.setText(f"{prefix_white}Session 2{end} {prefix_red}Phase finale{end}")
            self.subtitle.setText(
                "Tours 6 à 11 — chaque joueur de la poule A affronte tous ceux de la "
                "poule B. Le tour 11 oppose les joueurs de même rang."
            )
            self.action_btn.setVisible(False)

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
        v.addWidget(self._standings_table(standings))
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
            lbl = QLabel(f"Poule {pool}")
            lbl.setObjectName("h2")
            box.addWidget(lbl)
            box.addWidget(self._standings_table(
                compute_standings(
                    self._players.values(),
                    self._matches,
                    pool=pool,
                    max_round=5,
                )
            ))
            cnt = QWidget()
            cnt.setLayout(box)
            row.addWidget(cnt)
        row_w = QWidget()
        row_w.setLayout(row)
        v.addWidget(row_w)
        return wrapper

    @staticmethod
    def _standings_table(standings: list[PlayerStanding]) -> QTableWidget:
        table = QTableWidget(len(standings), 6)
        table.setHorizontalHeaderLabels(["#", "Joueur", "J", "V", "Pts", "Diff sets"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for row, st in enumerate(standings):
            items = [
                QTableWidgetItem(str(row + 1)),
                QTableWidgetItem(st.player.name),
                QTableWidgetItem(str(st.played)),
                QTableWidgetItem(str(st.wins)),
                QTableWidgetItem(str(st.points)),
                QTableWidgetItem(f"{st.set_diff:+d}"),
            ]
            for col, item in enumerate(items):
                if col != 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, col, item)
        table.resizeColumnsToContents()
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(40 + 36 * len(standings))
        return table
