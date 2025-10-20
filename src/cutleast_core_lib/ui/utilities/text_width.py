"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QWidget


def measure_text_width(widget: QWidget, text: str) -> int:
    """
    Calculates the approximate pixel width required to render the given text
    using the widget's current font and respecting the system's DPI scaling.

    Args:
        widget (QWidget): Any widget whose font metrics should be used.
        text (str): The text to measure.

    Returns:
        int: The width in device pixels required to render the text.
    """

    if not text.strip():
        return 0

    # QFontMetrics automatically scales with DPI for the widget's device
    fm = QFontMetrics(widget.font())
    width = fm.horizontalAdvance(text)

    # add a small padding to avoid clipping in tight layouts
    return width + 4
