"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QComboBox


class Dropdown(QComboBox):
    """
    A custom QComboBox where the scroll wheel has no effect.
    """

    @override
    def wheelEvent(self, e: QWheelEvent) -> None:
        e.ignore()
