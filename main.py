"""Top12 — Application de gestion de tournoi de tennis de table."""
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from src.database import Database
from src.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Top12")

    data_dir = Path.home() / ".top12"
    data_dir.mkdir(exist_ok=True)
    db = Database(data_dir / "top12.db")

    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
