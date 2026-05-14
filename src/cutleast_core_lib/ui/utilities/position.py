"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import QApplication

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum


class Position(LocalizedEnum):
    """Enum for widget anchor positions relative to a reference area."""

    Top = "top"
    """Centered at the top."""

    Bottom = "bottom"
    """Centered at the bottom."""

    Left = "left"
    """Centered on the left side."""

    Right = "right"
    """Centered on the right side."""

    TopLeft = "top_left"
    """Top-left corner."""

    TopRight = "top_right"
    """Top-right corner."""

    BottomLeft = "bottom_left"
    """Bottom-left corner."""

    BottomRight = "bottom_right"
    """Bottom-right corner."""

    @override
    def get_localized_name(self) -> str:
        locs: dict[Position, str] = {
            Position.Top: QApplication.translate("Position", "Top"),
            Position.Bottom: QApplication.translate("Position", "Bottom"),
            Position.Left: QApplication.translate("Position", "Left"),
            Position.Right: QApplication.translate("Position", "Right"),
            Position.TopLeft: QApplication.translate("Position", "Top Left"),
            Position.TopRight: QApplication.translate("Position", "Top Right"),
            Position.BottomLeft: QApplication.translate("Position", "Bottom Left"),
            Position.BottomRight: QApplication.translate("Position", "Bottom Right"),
        }

        return locs[self]
