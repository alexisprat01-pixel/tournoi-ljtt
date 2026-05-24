"""Statistics page — fun awards across the tournament."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from ..models import Match, Player
from ..stats import (
    compute_best_perf, compute_defender, compute_marathon, compute_showmen,
    compute_troublemaker,
)
from .styles import GREY, GREY_DARK, GREY_LIGHT, RED, TEXT, TEXT_DIM


# Each entry: (key, title, tooltip description, computer fn, formatter fn)
def _entries(players: list[Player], matches: list[Match]) -> list[dict]:
    return [
        {
            "title": "🏃 Le marathonien",
            "tooltip": (
                "Joueur ayant disputé le plus de points au total — "
                "chaque rallye d'un set compte pour les 2 joueurs."
            ),
            "results": compute_marathon(players, matches),
            "format": _fmt_marathon,
        },
        {
            "title": "🛡 Le défenseur",
            "tooltip": (
                "Joueur ayant perdu le moins de sets sur l'ensemble de la compétition."
            ),
            "results": compute_defender(players, matches),
            "format": _fmt_defender,
        },
        {
            "title": "📈 Le trouble-fête",
            "tooltip": (
                "Joueur avec la plus belle progression entre le classement de départ "
                "(par points d'inscription) et le classement actuel."
            ),
            "results": compute_troublemaker(players, matches),
            "format": _fmt_trouble,
        },
        {
            "title": "🎭 Les showmen",
            "tooltip": (
                "Match dans lequel il y a eu le plus de points joués au total — "
                "tous sets confondus, 2 joueurs additionnés."
            ),
            "results": compute_showmen(players, matches),
            "format": _fmt_showmen,
        },
        {
            "title": "💥 La perf",
            "tooltip": (
                "Joueur ayant battu un adversaire avec le plus gros écart de points "
                "d'inscription en sa défaveur (points adversaire − ses propres points)."
            ),
            "results": compute_best_perf(players, matches),
            "format": _fmt_perf,
        },
    ]


# ----- Formatters: return one human-readable HTML line per result -----

def _name(text: str) -> str:
    """Wrap a player name so it pops typographically (13pt semi-bold) —
    same treatment as the standings tables."""
    return f"<span style='font-size:13pt; font-weight:600;'>{text}</span>"


def _fmt_marathon(r: dict) -> str:
    return f"{_name(r['player'].name)} — {r['points']} points joués · {r['sets']} sets"


def _fmt_defender(r: dict) -> str:
    n = r["sets_lost"]
    plural = "sets perdus" if n != 1 else "set perdu"
    return f"{_name(r['player'].name)} — {n} {plural} (sur {r['played']} matchs)"


def _fmt_trouble(r: dict) -> str:
    return (
        f"{_name(r['player'].name)} — du rang {r['init_rank']} au rang "
        f"{r['final_rank']} (+{r['progression']} "
        f"place{'s' if r['progression'] > 1 else ''})"
    )


def _fmt_showmen(r: dict) -> str:
    p1 = _name(r["p1"].name) if r["p1"] else "?"
    p2 = _name(r["p2"].name) if r["p2"] else "?"
    return (
        f"{p1} vs {p2} — {r['points']} points joués · "
        f"{r['sets']} sets ({r['score1']}-{r['score2']})"
    )


def _fmt_perf(r: dict) -> str:
    w = _name(r["winner"].name)
    l = _name(r["loser"].name)
    return (
        f"{w} a battu {l}  (+{r['diff']} pts d'écart : "
        f"{w} {r['winner'].points} pts vs {l} {r['loser'].points} pts)"
    )


class StatisticsPage(QWidget):
    """Shows the fun awards of the tournament."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._players: list[Player] = []
        self._matches: list[Match] = []
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        head = QVBoxLayout()
        head.setContentsMargins(32, 24, 32, 0)
        title = QLabel(
            f"<span style='color:{TEXT};'>Top12</span> "
            f"<span style='color:{RED};'>Statistiques</span>"
        )
        title.setObjectName("h1")
        head.addWidget(title)
        self.subtitle = QLabel("")
        self.subtitle.setObjectName("muted")
        self.subtitle.setWordWrap(True)
        head.addWidget(self.subtitle)
        outer.addLayout(head)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(32, 16, 32, 24)
        self.content_layout.setSpacing(14)
        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll, 1)

    def set_data(self, players: list[Player], matches: list[Match]):
        self._players = list(players)
        self._matches = list(matches)
        self._render()

    def _clear(self):
        while self.content_layout.count():
            it = self.content_layout.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()

    def _render(self):
        self._clear()
        played_count = sum(1 for m in self._matches if m.played)
        if played_count == 0:
            self.subtitle.setText(
                "Aucun match joué pour le moment. Les statistiques s'animeront "
                "dès que des scores seront saisis."
            )
            self.content_layout.addStretch()
            return
        self.subtitle.setText(
            f"{played_count} match{'s' if played_count > 1 else ''} joué"
            f"{'s' if played_count > 1 else ''} — les prix se mettent à jour en direct."
        )
        for entry in _entries(self._players, self._matches):
            self.content_layout.addWidget(self._build_card(entry))
        self.content_layout.addStretch()

    @staticmethod
    def _build_card(entry: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 14)
        cl.setSpacing(6)

        head = QHBoxLayout()
        head.setSpacing(8)
        title = QLabel(entry["title"])
        title.setStyleSheet(
            f"color:{RED}; font-size:13pt; font-weight:bold; background:transparent;"
        )
        head.addWidget(title)
        help_lbl = QLabel("?")
        help_lbl.setFixedSize(18, 18)
        help_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_lbl.setCursor(Qt.CursorShape.WhatsThisCursor)
        help_lbl.setStyleSheet(
            f"background-color:{GREY_LIGHT}; color:{TEXT}; border-radius:9px; "
            "font-size:9pt; font-weight:bold;"
        )
        help_lbl.setToolTip(entry["tooltip"])
        head.addWidget(help_lbl)
        head.addStretch()
        head_w = QWidget()
        head_w.setLayout(head)
        head_w.setStyleSheet("background:transparent;")
        cl.addWidget(head_w)

        results = entry["results"]
        formatter = entry["format"]
        if not results:
            empty = QLabel("Pas encore de donnée disponible.")
            empty.setStyleSheet(
                f"color:{TEXT_DIM}; font-style:italic; background:transparent;"
            )
            cl.addWidget(empty)
        else:
            for r in results:
                line = QLabel(formatter(r))
                line.setStyleSheet(
                    f"color:{TEXT}; font-size:11pt; padding:2px 0; background:transparent;"
                )
                line.setWordWrap(True)
                cl.addWidget(line)
        return card
