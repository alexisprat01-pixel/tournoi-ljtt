"""Application stylesheet — V6 Editorial / Hero theme.

Rollback :
  - thème précédent conservé dans styles_legacy.py
  - ``git revert <ce commit>`` revient à l'ancien thème
  - ou ``git checkout pre-editorial-theme`` pour explorer
"""
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QRadialGradient
from PyQt6.QtWidgets import QWidget


# ===== Palette V6 (Editorial / Hero) =====

# Brand reds — used for buttons, focus, accents.
RED = "#FF3D2E"
RED_DARK = "#C8102E"
RED_GLOW = "#A8081A"           # used for the radial glow behind the page

# Neutral grays — warmer, slightly violet-tinged graphite
BLACK = "#08060A"               # main page background
GREY_DARK = "#0F0B12"           # sidebar background
GREY = "#15101A"                # cards, surfaces
GREY_LIGHT = "#2B1B26"          # hairlines, borders, separators
TEXT = "#FFFFFF"
TEXT_DIM = "#A89BA0"


# Border radius — pills for buttons, generous on cards.
PILL_RADIUS = 22
CARD_RADIUS = 14
INPUT_RADIUS = 10


STYLESHEET = f"""
/* Most widgets are transparent so the radial glow can shine through.
   Specific surfaces (sidebar, cards, inputs, etc.) set their own background. */
QWidget {{
    color: {TEXT};
    font-family: "Segoe UI", "Helvetica", sans-serif;
    font-size: 11pt;
}}

QMainWindow {{
    background-color: {BLACK};
}}

#sidebar {{
    background-color: {GREY_DARK};
    border-right: 1px solid {GREY_LIGHT};
}}

/* Sidebar nav buttons — flat with left accent on active (matches the section
   headers TOURNOI / NAVIGATION / ACTIONS). No filled background to keep the
   sidebar quiet and readable. */
#sidebar QPushButton {{
    background-color: transparent;
    color: {TEXT_DIM};
    text-align: left;
    padding: 10px 18px;
    border: none;
    border-left: 3px solid transparent;
    font-size: 11pt;
}}
#sidebar QPushButton:hover {{
    color: {TEXT};
}}
#sidebar QPushButton:checked {{
    background-color: transparent;
    color: {RED};
    font-weight: bold;
    border-left: 3px solid {RED};
}}

#sidebarLogo {{
    background-color: {GREY_DARK};
    padding: 16px;
}}

#sidebarTitle {{
    color: {RED};
    font-size: 16pt;
    font-weight: bold;
    padding: 14px 18px 4px 18px;
    background-color: {GREY_DARK};
    letter-spacing: 2px;
}}
#sidebarSubtitle {{
    color: {TEXT_DIM};
    font-size: 9pt;
    padding: 0 18px 12px 18px;
    background-color: {GREY_DARK};
}}

/* Primary action button — bright red pill */
QPushButton {{
    background-color: {RED};
    color: white;
    border: none;
    padding: 10px 22px;
    border-radius: {PILL_RADIUS}px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {RED_DARK};
}}
QPushButton:disabled {{
    background-color: {GREY_LIGHT};
    color: {TEXT_DIM};
}}

/* Secondary action — outline pill */
QPushButton#secondary {{
    background-color: transparent;
    color: {TEXT};
    border: 1px solid {GREY_LIGHT};
}}
QPushButton#secondary:hover {{
    background-color: {GREY};
    border-color: {RED};
    color: white;
}}

QLineEdit, QSpinBox, QTextEdit, QDateEdit, QPlainTextEdit {{
    background-color: {GREY};
    color: {TEXT};
    border: 1px solid {GREY_LIGHT};
    border-radius: {INPUT_RADIUS}px;
    padding: 8px 12px;
    min-height: 22px;
    selection-background-color: {RED};
    selection-color: white;
}}
QLineEdit:focus, QSpinBox:focus, QTextEdit:focus, QDateEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {RED};
}}

/* Date picker dropdown arrow + popup calendar */
QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {GREY_LIGHT};
}}
QCalendarWidget QWidget {{
    background-color: {GREY_DARK};
    color: {TEXT};
}}
QCalendarWidget QAbstractItemView:enabled {{
    background-color: {GREY_DARK};
    color: {TEXT};
    selection-background-color: {RED};
    selection-color: white;
}}
QCalendarWidget QAbstractItemView:disabled {{
    color: {GREY_LIGHT};
}}
/* Buttons in the calendar header — transparent so they blend with the
   navigation bar instead of creating grey rectangles inside the bar. */
QCalendarWidget QToolButton {{
    background-color: transparent;
    color: {TEXT};
    border: none;
    padding: 4px 10px;
    border-radius: 4px;
    font-weight: bold;
}}
QCalendarWidget QToolButton:hover {{
    background-color: {GREY_DARK};
    color: {RED};
}}
/* Prev/next month — we replace the native icon with "‹" / "›" text in code,
   here we just make sure the glyph is large and white. */
QCalendarWidget QToolButton#qt_calendar_prevmonth,
QCalendarWidget QToolButton#qt_calendar_nextmonth {{
    color: {TEXT};
    font-size: 16pt;
    qproperty-iconSize: 0px 0px;
}}
QCalendarWidget QMenu {{
    background-color: {GREY_DARK};
    color: {TEXT};
}}
QCalendarWidget QSpinBox {{
    background-color: {GREY};
    color: {TEXT};
}}
QCalendarWidget #qt_calendar_navigationbar {{
    background-color: {GREY};
}}

/* Checkboxes — dark, with a red check mark when ticked */
QCheckBox {{
    color: {TEXT};
    spacing: 8px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {GREY_LIGHT};
    border-radius: 4px;
    background-color: {GREY};
}}
QCheckBox::indicator:hover {{
    border-color: {RED};
}}
QCheckBox::indicator:checked {{
    background-color: {RED};
    border-color: {RED};
    image: none;
}}
QCheckBox:disabled {{
    color: {TEXT_DIM};
}}

QLabel#h1 {{
    font-size: 26pt;
    font-weight: bold;
    color: {TEXT};
    padding-bottom: 4px;
}}
QLabel#h2 {{
    font-size: 14pt;
    font-weight: bold;
    color: {RED};
    padding: 12px 0 6px 0;
    letter-spacing: 1px;
}}
QLabel#muted {{
    color: {TEXT_DIM};
}}

QFrame#card {{
    background-color: {GREY};
    border: 1px solid {GREY_LIGHT};
    border-radius: {CARD_RADIUS}px;
}}

QTableWidget {{
    background-color: {GREY};
    color: {TEXT};
    gridline-color: {GREY_LIGHT};
    border: 1px solid {GREY_LIGHT};
    border-radius: {CARD_RADIUS}px;
    selection-background-color: {RED_DARK};
}}
QTableWidget::item {{
    background-color: {GREY};
    color: {TEXT};
    padding: 6px;
}}
QHeaderView::section {{
    background-color: {GREY_DARK};
    color: {RED};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {RED};
    font-weight: bold;
    letter-spacing: 1px;
}}
/* Round the outer corners of the header so it doesn't paint square
   over the table's rounded card. */
QHeaderView::section:first {{
    border-top-left-radius: {CARD_RADIUS}px;
}}
QHeaderView::section:last {{
    border-top-right-radius: {CARD_RADIUS}px;
}}
QTableCornerButton::section {{
    background-color: {GREY_DARK};
    border: none;
    border-top-left-radius: {CARD_RADIUS}px;
}}

/* Container widgets must be transparent so the radial glow shines through
   them. Cards, tables and inputs keep their solid background because their
   selectors are more specific. */
QStackedWidget {{
    background-color: transparent;
}}
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}
QScrollBar:vertical {{
    background-color: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background-color: {GREY_LIGHT};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {RED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* Dialogs use a solid graphite bg (no glow) so they read clearly above the
   main window's hero glow. */
QDialog {{
    background-color: {GREY_DARK};
}}
QMessageBox {{
    background-color: {GREY_DARK};
}}
QMessageBox QLabel,
QDialog QLabel {{
    color: {TEXT};
}}

QFrame#matchCard {{
    background-color: {GREY};
    border: 1px solid {GREY_LIGHT};
    border-left: 4px solid {RED};
    border-radius: {CARD_RADIUS}px;
}}
QFrame#matchCard[played="true"] {{
    border-left: 4px solid #4CAF50;
}}
"""


# ===== Glow background widget =====

class GlowBackground(QWidget):
    """Page background with a subtle red radial glow in the top-right corner.

    Use as the central widget of QMainWindow (or wrap your content in it) to
    get the editorial "hero" backdrop. Other widgets are painted on top with
    their own styled backgrounds.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        bg: str = BLACK,
        glow_color: str = RED_GLOW,
        corner: str = "top-right",
        intensity: int = 140,
    ):
        super().__init__(parent)
        self._bg = QColor(bg)
        self._glow = QColor(glow_color)
        self._corner = corner
        self._intensity = intensity
        # We paint the entire widget surface ourselves — tell Qt to skip
        # its own background clearing (which would otherwise show the native
        # palette colour, often white on Windows).
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAutoFillBackground(False)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), self._bg)
        w, h = self.width(), self.height()
        if self._corner == "top-right":
            center = QPointF(w * 0.78, h * 0.18)
        elif self._corner == "top-left":
            center = QPointF(w * 0.20, h * 0.18)
        else:
            center = QPointF(w * 0.5, h * 0.5)
        radius = max(w, h) * 0.55
        g = QRadialGradient(center, radius)
        c0 = QColor(self._glow)
        c0.setAlpha(self._intensity)
        g.setColorAt(0.0, c0)
        c_mid = QColor(self._glow)
        c_mid.setAlpha(35)
        g.setColorAt(0.5, c_mid)
        end = QColor(0, 0, 0, 0)
        g.setColorAt(1.0, end)
        p.fillRect(self.rect(), g)
        p.end()
