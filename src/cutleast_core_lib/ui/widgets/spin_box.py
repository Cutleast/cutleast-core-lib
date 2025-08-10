"""
Copyright (c) Cutleast
"""

from typing import Any, override

from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QSpinBox


class SpinBox(QSpinBox):
    """
    A custom QSpinBox which requires strong focus for the scroll wheel to have any
    effect.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    @override
    def wheelEvent(self, event: QWheelEvent) -> None:
        if not self.hasFocus():
            event.ignore()
        else:
            super().wheelEvent(event)
