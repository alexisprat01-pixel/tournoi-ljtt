"""Application stylesheet — red and black club theme."""

RED = "#C8102E"
RED_DARK = "#8E0B20"
BLACK = "#0E0E10"
GREY_DARK = "#1B1B1F"
GREY = "#2A2A30"
GREY_LIGHT = "#3A3A42"
TEXT = "#F2F2F2"
TEXT_DIM = "#B4B4B8"

STYLESHEET = f"""
QWidget {{
    background-color: {BLACK};
    color: {TEXT};
    font-family: "Segoe UI", "Helvetica", sans-serif;
    font-size: 11pt;
}}

QMainWindow {{
    background-color: {BLACK};
}}

#sidebar {{
    background-color: {GREY_DARK};
    border-right: 2px solid {RED};
}}

#sidebar QPushButton {{
    background-color: transparent;
    color: {TEXT};
    text-align: left;
    padding: 12px 18px;
    border: none;
    border-left: 4px solid transparent;
    font-size: 11pt;
}}
#sidebar QPushButton:hover {{
    background-color: {GREY};
}}
#sidebar QPushButton:checked {{
    background-color: {GREY};
    border-left: 4px solid {RED};
    color: {RED};
    font-weight: bold;
}}

#sidebarLogo {{
    background-color: {GREY_DARK};
    padding: 16px;
}}

#sidebarTitle {{
    color: {RED};
    font-size: 18pt;
    font-weight: bold;
    padding: 16px 18px 4px 18px;
    background-color: {GREY_DARK};
}}
#sidebarSubtitle {{
    color: {TEXT_DIM};
    font-size: 9pt;
    padding: 0 18px 12px 18px;
    background-color: {GREY_DARK};
}}

QPushButton {{
    background-color: {RED};
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {RED_DARK};
}}
QPushButton:disabled {{
    background-color: {GREY_LIGHT};
    color: {TEXT_DIM};
}}

QPushButton#secondary {{
    background-color: {GREY};
    color: {TEXT};
}}
QPushButton#secondary:hover {{
    background-color: {GREY_LIGHT};
}}

QLineEdit, QSpinBox {{
    background-color: {GREY_DARK};
    color: {TEXT};
    border: 1px solid {GREY_LIGHT};
    border-radius: 4px;
    padding: 8px 10px;
    min-height: 22px;
    selection-background-color: {RED};
}}
QLineEdit:focus, QSpinBox:focus {{
    border: 1px solid {RED};
}}

QLabel#h1 {{
    font-size: 20pt;
    font-weight: bold;
    color: {TEXT};
    padding-bottom: 4px;
}}
QLabel#h2 {{
    font-size: 14pt;
    font-weight: bold;
    color: {RED};
    padding: 12px 0 6px 0;
}}
QLabel#muted {{
    color: {TEXT_DIM};
}}

QFrame#card {{
    background-color: {GREY_DARK};
    border: 1px solid {GREY_LIGHT};
    border-radius: 6px;
}}

QTableWidget {{
    background-color: {GREY_DARK};
    color: {TEXT};
    gridline-color: {GREY_LIGHT};
    border: 1px solid {GREY_LIGHT};
    border-radius: 4px;
    selection-background-color: {RED_DARK};
}}
QTableWidget::item {{
    padding: 6px;
}}
QHeaderView::section {{
    background-color: {GREY};
    color: {RED};
    padding: 8px;
    border: none;
    border-bottom: 2px solid {RED};
    font-weight: bold;
}}

QScrollArea {{
    border: none;
    background-color: {BLACK};
}}
QScrollBar:vertical {{
    background-color: {GREY_DARK};
    width: 12px;
}}
QScrollBar::handle:vertical {{
    background-color: {GREY_LIGHT};
    border-radius: 6px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {RED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QMessageBox {{
    background-color: {GREY_DARK};
}}
QMessageBox QLabel {{
    color: {TEXT};
}}

QFrame#matchCard {{
    background-color: {GREY_DARK};
    border: 1px solid {GREY_LIGHT};
    border-left: 4px solid {RED};
    border-radius: 4px;
}}
QFrame#matchCard[played="true"] {{
    border-left: 4px solid #4CAF50;
}}
"""
