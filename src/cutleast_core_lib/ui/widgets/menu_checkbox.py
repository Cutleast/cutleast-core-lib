"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QCheckBox


class MenuCheckBox(QCheckBox):
    """
    Checkbox whose complete widget area toggles its state.
    """

    @override
    def hitButton(self, position: QPoint) -> bool:
        """
        Checks whether a position is within the complete checkbox widget.

        Args:
            position (QPoint): Position relative to the checkbox.

        Returns:
            bool: Whether the position toggles the checkbox.
        """

        return self.rect().contains(position)
