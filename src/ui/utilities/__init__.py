"""
Copyright (c) Cutleast
"""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget


def apply_shadow(widget: QWidget, size: int = 4, shadow_color: str = "#181818") -> None:
    """
    Applies standardized shadow effect to a widget. Replaces existing graphics effects.

    Args:
        widget (QWidget): Widget to apply shadow
        size (int, optional): Shadow size. Defaults to 4.
        shadow_color (str, optional): Shadow color. Defaults to "#181818".
    """

    shadoweffect = QGraphicsDropShadowEffect(widget)
    shadoweffect.setBlurRadius(size)
    shadoweffect.setXOffset(size)
    shadoweffect.setYOffset(size)
    shadoweffect.setColor(QColor.fromString(shadow_color))
    widget.setGraphicsEffect(shadoweffect)
