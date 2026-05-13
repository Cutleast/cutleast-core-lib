"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Callable

from pydantic import BaseModel
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget


class ColumnConfig(BaseModel, frozen=True):
    """
    Model for the configuration of a column in a tree widget.
    """

    index: int
    """The index of the column in the tree widget."""

    title_supplier: Callable[[], str]
    """A callable that returns the title of the column."""

    alignment: Qt.AlignmentFlag = (
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    )
    """The alignment of the column header and items in the column."""

    width: int = 100
    """The initial width of the column in pixels."""


class ColumnEnum(Enum):
    """
    Base class for column enums.
    """

    # this constraints subclass members to be of type ColumnConfig
    _value_: ColumnConfig

    # this is required to satisfy pyright's type checking for the value attribute of the
    # enum members, which is expected to be of type ColumnConfig
    value: ColumnConfig  # pyright: ignore[reportIncompatibleMethodOverride]

    @classmethod
    def apply_to_tree_widget(cls, tree_widget: QTreeWidget) -> None:
        """
        Apply the column configuration to the given tree widget.

        Args:
            tree_widget: The tree widget to apply the column configuration to.
        """

        columns: list[ColumnConfig] = sorted(
            (column.value for column in cls), key=lambda config: config.index
        )

        tree_widget.setColumnCount(len(columns))
        tree_widget.setHeaderLabels([column.title_supplier() for column in columns])

        for col in columns:
            tree_widget.setColumnWidth(col.index, col.width)
            tree_widget.headerItem().setTextAlignment(col.index, col.alignment)

    @property
    def index(self) -> int:
        """The index of the column."""

        return self.value.index

    @property
    def title(self) -> str:
        """The title of the column."""

        return self.value.title_supplier()

    @property
    def alignment(self) -> Qt.AlignmentFlag:
        """The alignment of the column."""

        return self.value.alignment

    @property
    def width(self) -> int:
        """The initial width of the column in pixels."""

        return self.value.width
