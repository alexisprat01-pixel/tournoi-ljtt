"""Tournoi LJTT — Application de gestion de tournois de tennis de table."""
import shutil
import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from src.database import Database
from src.ui import styles
from src.ui.main_window import MainWindow


def _assets_dir() -> Path:
    """Resolve the assets directory both in dev mode and inside a PyInstaller bundle."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / "src" / "assets"
    return Path(__file__).resolve().parent / "src" / "assets"


def _apply_windows_taskbar_icon():
    """On Windows the taskbar groups apps by AppUserModelID — set ours explicitly
    so the .exe shows our icon instead of being grouped under the generic Python
    interpreter."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("club.ljtt.tournoi")
    except Exception:
        pass  # not fatal — icon may just fall back to the default group


def _resolve_data_dir() -> Path:
    """Use ~/.tournoi-ljtt/ as the canonical data directory.

    If only the legacy ~/.top12/ exists, migrate its top12.db over once so
    that users who already used the previous build don't lose their work.
    The legacy directory is left untouched — manual cleanup if needed.
    """
    new_dir = Path.home() / ".tournoi-ljtt"
    new_dir.mkdir(exist_ok=True)
    new_db = new_dir / "tournoi-ljtt.db"

    legacy_db = Path.home() / ".top12" / "top12.db"
    if not new_db.exists() and legacy_db.exists():
        try:
            shutil.copy2(legacy_db, new_db)
        except OSError:
            pass  # if copy fails we'll just start with an empty DB
    return new_dir


def main():
    _apply_windows_taskbar_icon()

    app = QApplication(sys.argv)
    app.setApplicationName("Tournoi LJTT")
    styles.load_fonts(app)

    assets = _assets_dir()
    icon_path = assets / "icon.ico"
    if not icon_path.exists():
        icon_path = assets / "logo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    data_dir = _resolve_data_dir()
    db = Database(data_dir / "tournoi-ljtt.db")

    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
