"""Dialog helpers with French button labels."""
from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox, QWidget


def confirm(parent: QWidget | None, title: str, text: str, default_yes: bool = True) -> bool:
    """Yes/No confirmation dialog with French button labels."""
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setIcon(QMessageBox.Icon.Question)
    yes = box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
    no = box.addButton("Non", QMessageBox.ButtonRole.NoRole)
    box.setDefaultButton(yes if default_yes else no)
    box.exec()
    return box.clickedButton() is yes
