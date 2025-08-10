"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Qt

from .log_widget import LogWidget


class LogWindow(LogWidget):
    """
    A window for displaying the application log in realtime.
    """

    def __init__(self, initial_text: str = "") -> None:
        super().__init__(initial_text)

        self.setWindowTitle(self.tr("Log"))
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.resize(600, 400)
