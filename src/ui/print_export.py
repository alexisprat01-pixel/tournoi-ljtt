"""Print preview / PDF export of match slips for a session.

Layout (V4) — 10 strips per A4 page, one match per strip:

    ┌──────────────────────────────────────────────────────────────┐
    │ [T1]  R3   Alice Martin    ┌─┬─┬─┬─┬─┐   Arb. Marc Dupont    │
    │            Bob Leroux      └─┴─┴─┴─┴─┘                       │
    └──────────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPageLayout, QPageSize, QPainter, QPen
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter
from PyQt6.QtWidgets import QMessageBox, QWidget

from ..models import Match, Player


TABLE_COLORS = {1: "#C8102E", 2: "#1E88E5", 3: "#43A047"}

# Strip layout (everything in millimetres). Tweak here for cell size, font…
STRIPS_PER_PAGE = 10
STRIP_GAP_MM = 1.5
PAGE_MARGIN_MM = 12
TABLE_CHIP_W_MM = 10
ROUND_BADGE_W_MM = 8
NAMES_W_MM = 60
CELL_W_MM = 11
N_CELLS = 5
GRID_W_MM = CELL_W_MM * N_CELLS
REF_W_MM = 45


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

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    printer.setPageMargins(
        PAGE_MARGIN_MM, PAGE_MARGIN_MM, PAGE_MARGIN_MM, PAGE_MARGIN_MM,
        QPageLayout.Unit.Millimeter,
    )
    printer.setDocName(f"top12-session-{session}-matchs")

    preview = QPrintPreviewDialog(printer, parent)
    preview.setWindowTitle(f"Imprimer — Session {session}")
    preview.resize(960, 1120)

    players_by_id: dict[int, Player] = {p.id: p for p in players}

    def paint(printer_obj: QPrinter):
        painter = QPainter(printer_obj)
        try:
            _draw_session(painter, printer_obj, matches, players_by_id, session)
        finally:
            painter.end()

    preview.paintRequested.connect(paint)
    preview.exec()


# ----- Rendering -----

def _draw_session(
    painter: QPainter,
    printer: QPrinter,
    matches: list[Match],
    players_by_id: dict[int, Player],
    session: int,
):
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Work in millimetres regardless of the device DPI.
    page_rect_mm = printer.pageLayout().paintRect(QPageLayout.Unit.Millimeter)
    # The page rect already excludes the margin; treat its top-left as (0, 0).
    page_w_mm = page_rect_mm.width()
    page_h_mm = page_rect_mm.height()

    dpi = printer.resolution()
    mm_to_px = dpi / 25.4

    def mm_rect(x_mm, y_mm, w_mm, h_mm):
        return QRectF(x_mm * mm_to_px, y_mm * mm_to_px,
                      w_mm * mm_to_px, h_mm * mm_to_px)

    strip_h_mm = page_h_mm / STRIPS_PER_PAGE

    for i, m in enumerate(matches):
        slot = i % STRIPS_PER_PAGE
        if i > 0 and slot == 0:
            printer.newPage()

        y_mm = slot * strip_h_mm + STRIP_GAP_MM / 2
        strip = mm_rect(0, y_mm, page_w_mm, strip_h_mm - STRIP_GAP_MM)
        _draw_strip(painter, strip, m, players_by_id, mm_to_px)


def _draw_strip(
    painter: QPainter,
    rect: QRectF,
    match: Match,
    players_by_id: dict[int, Player],
    mm_to_px: float,
):
    # ---- border ----
    painter.setPen(QPen(QColor("#222"), 1.4 * mm_to_px * 0.4))
    painter.setBrush(Qt.GlobalColor.transparent)
    painter.drawRoundedRect(rect, 2 * mm_to_px, 2 * mm_to_px)

    # Pixels-per-mm shorthand
    M = mm_to_px

    pad = 2 * M
    inner_top = rect.top() + 1.5 * M
    inner_bot = rect.bottom() - 1.5 * M
    inner_h = inner_bot - inner_top

    # ---- table chip ----
    chip_w = TABLE_CHIP_W_MM * M
    chip = QRectF(rect.left() + pad, inner_top, chip_w, inner_h)
    color = QColor(TABLE_COLORS.get(match.table_number, "#666"))
    painter.fillRect(chip, color)
    painter.setPen(QColor("white"))
    painter.setFont(QFont("Arial", int(M * 4), QFont.Weight.Bold))
    painter.drawText(chip, Qt.AlignmentFlag.AlignCenter, f"T{match.table_number}")

    # ---- round badge ----
    round_x = chip.right() + 2 * M
    round_rect = QRectF(round_x, inner_top, ROUND_BADGE_W_MM * M, inner_h)
    painter.setPen(QColor("#555"))
    painter.setFont(QFont("Arial", int(M * 3), QFont.Weight.Bold))
    painter.drawText(round_rect, Qt.AlignmentFlag.AlignCenter,
                     f"R{match.round_number}")

    # ---- player names (stacked, aligned with score rows) ----
    p1 = players_by_id.get(match.player1_id)
    p2 = players_by_id.get(match.player2_id)
    names_x = round_rect.right() + 2 * M
    names_w = NAMES_W_MM * M
    row_h = inner_h / 2
    p1_rect = QRectF(names_x, inner_top, names_w, row_h)
    p2_rect = QRectF(names_x, inner_top + row_h, names_w, row_h)

    painter.setPen(QColor("#000"))
    painter.setFont(QFont("Arial", int(M * 3.8), QFont.Weight.Bold))
    if p1:
        painter.drawText(p1_rect,
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         p1.name)
    if p2:
        painter.drawText(p2_rect,
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         p2.name)

    # ---- score grid (5 sets × 2 rows) ----
    grid_x = names_x + names_w + 2 * M
    grid_w = GRID_W_MM * M
    cell_w = grid_w / N_CELLS
    painter.setPen(QPen(QColor("#000"), 1.0))
    for col in range(N_CELLS):
        for row in range(2):
            cell = QRectF(grid_x + col * cell_w, inner_top + row * row_h,
                          cell_w, row_h)
            painter.drawRect(cell)

    # ---- referee on the right ----
    ref = players_by_id.get(match.referee_id) if match.referee_id else None
    ref_x = grid_x + grid_w + 3 * M
    ref_w = rect.right() - ref_x - pad
    painter.setFont(QFont("Arial", int(M * 3), QFont.Weight.Normal))
    painter.setPen(QColor("#555"))
    ref_text = f"Arb. {ref.name}" if ref else ""
    painter.drawText(QRectF(ref_x, inner_top, ref_w, inner_h),
                     Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                     ref_text)
