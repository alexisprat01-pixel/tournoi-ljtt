"""Print preview / PDF export of match slips for a session.

Layout (V4) — 10 strips per A4 page, one match per strip:

    ┌──────────────────────────────────────────────────────────────┐
    │ [T1]  R3   Alice Martin    ┌─┬─┬─┬─┬─┐   Arb. Marc Dupont    │
    │            Bob Leroux      └─┴─┴─┴─┴─┘                       │
    └──────────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import traceback

from PyQt6.QtCore import QMarginsF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPageLayout, QPageSize, QPainter, QPalette, QPen
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget

from ..models import Match, Player


TABLE_COLORS = {1: "#C8102E", 2: "#1E88E5", 3: "#43A047"}

# Strip layout (everything in millimetres). Grid: COLS_PER_PAGE × ROWS_PER_PAGE.
COLS_PER_PAGE = 2
ROWS_PER_PAGE = 10
STRIPS_PER_PAGE = COLS_PER_PAGE * ROWS_PER_PAGE   # = 20
PAGE_MARGIN_MM = 10
COL_GAP_MM = 4
ROW_GAP_MM = 1.5
TABLE_CHIP_W_MM = 8
ROUND_BADGE_W_MM = 6
NAMES_W_MM = 30
CELL_W_MM = 6
N_CELLS = 5
GRID_W_MM = CELL_W_MM * N_CELLS
REF_W_MM = 24


def open_match_print_preview(
    parent: QWidget,
    matches: list[Match],
    players: list[Player],
    session: int,
):
    """Display Qt's standard print preview dialog for the given matches.

    Through that dialog the user can either send the output to a real printer
    or hit the "Save as PDF" button (Windows shows it natively).
    """
    if not matches:
        QMessageBox.information(
            parent, "Rien à imprimer",
            "Aucun match à imprimer pour cette session.",
        )
        return

    app = QApplication.instance()
    saved_stylesheet = app.styleSheet() if app else ""
    try:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        # In Qt 6 setPageMargins expects a QMarginsF, not 4 floats.
        printer.setPageMargins(
            QMarginsF(PAGE_MARGIN_MM, PAGE_MARGIN_MM, PAGE_MARGIN_MM, PAGE_MARGIN_MM),
            QPageLayout.Unit.Millimeter,
        )
        printer.setDocName(f"top12-session-{session}-matchs")

        # Temporarily drop the app's stylesheet — it makes the QPrintPreviewDialog
        # toolbar buttons (Print, Save PDF, etc.) invisible because every QWidget
        # inherits white text on dark bg + the toolbar icons don't adapt.
        if app:
            app.setStyleSheet("")

        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle(f"Imprimer — Session {session}")
        preview.resize(960, 1120)
        # Force a light palette on the dialog so its toolbar icons (Print, Save PDF,
        # zoom, page-fit, etc.) render visibly against a light background, regardless
        # of the parent window's dark palette.
        light = QPalette()
        light.setColor(QPalette.ColorRole.Window, QColor("#F2F2F2"))
        light.setColor(QPalette.ColorRole.WindowText, QColor("#101010"))
        light.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        light.setColor(QPalette.ColorRole.Text, QColor("#101010"))
        light.setColor(QPalette.ColorRole.Button, QColor("#E6E6E6"))
        light.setColor(QPalette.ColorRole.ButtonText, QColor("#101010"))
        light.setColor(QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF"))
        light.setColor(QPalette.ColorRole.ToolTipText, QColor("#101010"))
        preview.setPalette(light)
        # Apply to all descendants (toolbar, buttons, spinbox, combobox).
        for child in preview.findChildren(QWidget):
            child.setPalette(light)

        players_by_id: dict[int, Player] = {p.id: p for p in players}

        def paint(printer_obj: QPrinter):
            painter = QPainter(printer_obj)
            try:
                _draw_session(painter, printer_obj, matches, players_by_id, session)
            finally:
                painter.end()

        preview.paintRequested.connect(paint)
        preview.exec()
    except Exception as e:
        QMessageBox.critical(
            parent, "Erreur d'impression",
            f"Impossible d'ouvrir l'aperçu d'impression :\n\n{e}\n\n"
            f"{traceback.format_exc()}",
        )
    finally:
        if app:
            app.setStyleSheet(saved_stylesheet)


# ----- Rendering -----

def _draw_session(
    painter: QPainter,
    printer: QPrinter,
    matches: list[Match],
    players_by_id: dict[int, Player],
    session: int,
):
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    page_rect_mm = printer.pageLayout().paintRect(QPageLayout.Unit.Millimeter)
    page_w_mm = page_rect_mm.width()
    page_h_mm = page_rect_mm.height()

    dpi = printer.resolution()
    mm_to_px = dpi / 25.4

    def mm_rect(x_mm, y_mm, w_mm, h_mm):
        return QRectF(x_mm * mm_to_px, y_mm * mm_to_px,
                      w_mm * mm_to_px, h_mm * mm_to_px)

    # Grid of COLS_PER_PAGE × ROWS_PER_PAGE strips with gaps in between.
    total_col_gap = COL_GAP_MM * (COLS_PER_PAGE - 1)
    col_w_mm = (page_w_mm - total_col_gap) / COLS_PER_PAGE
    row_h_mm = page_h_mm / ROWS_PER_PAGE

    for i, m in enumerate(matches):
        slot = i % STRIPS_PER_PAGE
        if i > 0 and slot == 0:
            printer.newPage()
        row = slot // COLS_PER_PAGE
        col = slot % COLS_PER_PAGE

        x_mm = col * (col_w_mm + COL_GAP_MM)
        y_mm = row * row_h_mm + ROW_GAP_MM / 2
        strip = mm_rect(x_mm, y_mm, col_w_mm, row_h_mm - ROW_GAP_MM)
        _draw_strip(painter, strip, m, players_by_id, mm_to_px)


def _draw_strip(
    painter: QPainter,
    rect: QRectF,
    match: Match,
    players_by_id: dict[int, Player],
    mm_to_px: float,
):
    M = mm_to_px  # pixels-per-mm shorthand

    # ---- border ----
    painter.setPen(QPen(QColor("#222"), 0.4 * M))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(rect, 1.5 * M, 1.5 * M)

    pad = 1.2 * M
    inner_top = rect.top() + 1 * M
    inner_bot = rect.bottom() - 1 * M
    inner_h = inner_bot - inner_top

    # ---- table chip ----
    chip_w = TABLE_CHIP_W_MM * M
    chip = QRectF(rect.left() + pad, inner_top, chip_w, inner_h)
    color = QColor(TABLE_COLORS.get(match.table_number, "#666"))
    painter.fillRect(chip, color)
    painter.setPen(QColor("white"))
    painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
    painter.drawText(chip, Qt.AlignmentFlag.AlignCenter, f"T{match.table_number}")

    # ---- round badge ----
    round_x = chip.right() + 1 * M
    round_rect = QRectF(round_x, inner_top, ROUND_BADGE_W_MM * M, inner_h)
    painter.setPen(QColor("#555"))
    painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
    painter.drawText(round_rect, Qt.AlignmentFlag.AlignCenter,
                     f"R{match.round_number}")

    # ---- player names (stacked, aligned with score rows) ----
    p1 = players_by_id.get(match.player1_id)
    p2 = players_by_id.get(match.player2_id)
    names_x = round_rect.right() + 1.2 * M
    names_w = NAMES_W_MM * M
    row_h = inner_h / 2
    p1_rect = QRectF(names_x, inner_top, names_w, row_h)
    p2_rect = QRectF(names_x, inner_top + row_h, names_w, row_h)

    painter.setPen(QColor("#000"))
    painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
    if p1:
        painter.drawText(p1_rect,
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         p1.name)
    if p2:
        painter.drawText(p2_rect,
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         p2.name)

    # ---- score grid (5 sets × 2 rows) ----
    grid_x = names_x + names_w + 1.2 * M
    grid_w = GRID_W_MM * M
    cell_w = grid_w / N_CELLS
    painter.setPen(QPen(QColor("#000"), 0.4 * M))
    for col in range(N_CELLS):
        for row in range(2):
            cell = QRectF(grid_x + col * cell_w, inner_top + row * row_h,
                          cell_w, row_h)
            painter.drawRect(cell)

    # ---- referee on the right (3 lines: "Arb." / prénom / nom) ----
    ref = players_by_id.get(match.referee_id) if match.referee_id else None
    ref_x = grid_x + grid_w + 1.5 * M
    ref_w = rect.right() - ref_x - pad
    line_h = inner_h / 3
    painter.setPen(QColor("#555"))
    # "Arb." label on top
    painter.setFont(QFont("Arial", 6, QFont.Weight.Normal))
    painter.drawText(QRectF(ref_x, inner_top, ref_w, line_h),
                     Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                     "Arb." if ref else "")
    if ref:
        # Split on first space: first token = prénom, reste = nom
        parts = ref.name.strip().split(" ", 1)
        prenom = parts[0]
        nom = parts[1] if len(parts) > 1 else ""
        painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        painter.setPen(QColor("#000"))
        painter.drawText(QRectF(ref_x, inner_top + line_h, ref_w, line_h),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         prenom)
        painter.drawText(QRectF(ref_x, inner_top + 2 * line_h, ref_w, line_h),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         nom)
