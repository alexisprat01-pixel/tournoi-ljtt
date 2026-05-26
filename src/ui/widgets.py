"""Small reusable UI helpers — currently just the editorial page header.

Used by every top-level page (home, joueurs, rounds, classement, stats)
to render the consistent header block:

    EYEBROW (rouge, majuscules)
    Titre serif avec un *mot accentué* en bordeaux italique
    Lead descriptif optionnel (serif, dim)
    ━━━━━━ hairline rouge
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from .styles import RED


def make_page_header(
    title: str,
    *,
    eyebrow: str | None = None,
    accent_word: str | None = None,
    lead: str | None = None,
    parent: QWidget | None = None,
) -> QWidget:
    """Build the editorial header block for a page.

    Args:
        title: the main heading text. Plain string — no HTML.
        eyebrow: optional small uppercase label rendered above the title in
            bordeaux. Uppercased defensively.
        accent_word: optional substring of ``title`` to render in italic
            bordeaux (Playfair italic). Case-sensitive. If not found, no
            accent is applied.
        lead: optional descriptive paragraph rendered below the title in
            dimmed Source Serif 4.
        parent: optional Qt parent.

    Returns the assembled QWidget — drop it into the page's outer layout.
    """
    container = QWidget(parent)
    v = QVBoxLayout(container)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(2)

    if eyebrow:
        eb = QLabel(eyebrow.upper())
        eb.setObjectName("eyebrow")
        v.addWidget(eb)

    if accent_word and accent_word in title:
        before, after = title.split(accent_word, 1)
        html = (
            f"{before}"
            f"<span style='color:{RED}; font-style:italic;'>{accent_word}</span>"
            f"{after}"
        )
        h1 = QLabel(html)
        h1.setTextFormat(Qt.TextFormat.RichText)
    else:
        h1 = QLabel(title)
    h1.setObjectName("h1")
    v.addWidget(h1)

    if lead:
        ld = QLabel(lead)
        ld.setObjectName("lead")
        ld.setWordWrap(True)
        v.addWidget(ld)

    rule = QFrame()
    rule.setObjectName("rule")
    rule.setFixedHeight(1)
    rule.setStyleSheet(f"background-color:{RED};")
    v.addWidget(rule)
    v.addSpacing(10)

    return container
