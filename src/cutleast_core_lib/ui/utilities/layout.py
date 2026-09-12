"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtWidgets import QLayout, QWidget


def clear_layout(layout: QLayout) -> None:
    """
    Clears a layout by removing all its direct children.

    Args:
        layout (QLayout): Layout to clear.
    """

    while (item := layout.takeAt(0)) is not None:
        widget: Optional[QWidget] = item.widget()
        if widget is not None:
            widget.setParent(None)

        item_layout: Optional[QLayout] = item.layout()
        if item_layout is not None:
            item_layout.setParent(None)
