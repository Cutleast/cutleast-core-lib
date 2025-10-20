"""
Copyright (c) Cutleast
"""

from collections.abc import Generator
from typing import Optional

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from .text_width import measure_text_width


def iter_children(item: QTreeWidgetItem) -> Generator[QTreeWidgetItem]:
    """
    Iterates over all children of a tree item.

    Args:
        item (QTreeWidgetItem): Tree item

    Yields:
        Generator[QTreeWidgetItem]: Tree items
    """

    for i in range(item.childCount()):
        yield item.child(i)


def iter_toplevel_items(widget: QTreeWidget) -> Generator[QTreeWidgetItem]:
    """
    Iterates over all top level items of a tree widget.

    Args:
        widget (QTreeWidget): Tree widget

    Yields:
        Generator[QTreeWidgetItem]: Tree items
    """

    for i in range(widget.topLevelItemCount()):
        item: Optional[QTreeWidgetItem] = widget.topLevelItem(i)
        if item is not None:
            yield item


def iter_all_items(widget: QTreeWidget) -> Generator[QTreeWidgetItem]:
    """
    Recursively iterates over all items in a QTreeWidget, including top-level
    and nested children.

    Args:
        widget (QTreeWidget): Tree widget to iterate.

    Yields:
        Generator[QTreeWidgetItem]: All tree items in depth-first order.
    """

    def _iter_item(item: QTreeWidgetItem) -> Generator[QTreeWidgetItem]:
        """
        Recursively yields a QTreeWidgetItem and all its children.
        """

        yield item
        for i in range(item.childCount()):
            child: Optional[QTreeWidgetItem] = item.child(i)
            if child is not None:
                yield from _iter_item(child)

    for i in range(widget.topLevelItemCount()):
        top_item: Optional[QTreeWidgetItem] = widget.topLevelItem(i)
        if top_item is not None:
            yield from _iter_item(top_item)


def are_children_visible(item: QTreeWidgetItem) -> bool:
    """
    Checks if any child of a tree item or its children is visible.

    Args:
        item (QTreeWidgetItem): Tree item

    Returns:
        bool: True if any child is visible, False otherwise
    """

    for child in iter_children(item):
        if child.childCount() > 0:
            if not child.isHidden() or are_children_visible(child):
                return True
        elif not child.isHidden():
            return True

    return False


def calculate_required_width(widget: QTreeWidget, column: int) -> int:
    """
    Calculates the approximate width required to full display the text of a column.

    Args:
        widget (QTreeWidget): Tree widget.
        column (int): Column.

    Returns:
        int: The width in pixels required to render the text.
    """

    texts: list[str] = [item.text(column) for item in iter_all_items(widget)]
    return measure_text_width(widget, max(texts, key=len))
