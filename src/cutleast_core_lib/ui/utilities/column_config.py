"""
Copyright (c) Cutleast
"""

from collections.abc import Callable
from enum import Enum
from typing import Any, Generic, Optional, Self, TypeAlias, TypeVar, cast, override

from pydantic import BaseModel
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon
from PySide6.QtWidgets import QHeaderView, QTreeWidget, QTreeWidgetItem

from cutleast_core_lib.core.utilities.typing_utils import Comparable

from .theme import HexColorStr

# required as Nuitka does not support the new generic class syntax yet
# TODO: Remove this once Nuitka supports it
M = TypeVar("M", bound=BaseModel)

Color: TypeAlias = QColor | Qt.GlobalColor | HexColorStr
"""Alias for all accepted types of colors."""


class CellValue(BaseModel, arbitrary_types_allowed=True, frozen=True):
    """
    Represents a value supplied by the owner of a tree item.

    Such values are not derived from the item's model and therefore persist
    when the item is updated.
    """

    display_text: str
    """Text displayed in the cell."""

    sort_key: Any
    """Value used when sorting the cell."""


class ColumnConfig(BaseModel, Generic[M], arbitrary_types_allowed=True, frozen=True):
    """
    Model for the configuration of a column in a tree widget.
    """

    title_supplier: Callable[[], str]
    """A callable that returns a localized title for the column."""

    display_text_getter: Callable[[M], str]
    """A callable that returns the display text for a model instance."""

    sort_key_getter: Optional[Callable[[M], Comparable]] = None
    """A callable that returns the value used for sorting a model instance."""

    tooltip_getter: Optional[Callable[[M], str]] = None
    """A callable that returns the tooltip text for a model instance."""

    icon_getter: Optional[Callable[[M], Optional[QIcon]]] = None
    """A callable that returns the icon for a model instance."""

    foreground_color_getter: Optional[Callable[[M], Optional[Color]]] = None
    """A callable that returns the foreground color for a model instance."""

    font_getter: Optional[Callable[[M], Optional[QFont]]] = None
    """A callable that returns the font for a model instance."""

    alignment_getter: Optional[Callable[[M], Qt.AlignmentFlag]] = None
    """A callable that returns the alignment for a model instance."""

    header_alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter
    """The alignment of the column header."""

    initial_width: Optional[int] = None
    """The initial width of the column in pixels."""

    stretch: bool = False
    """Whether the column should stretch to fill the available space."""

    def get_title(self) -> str:
        """
        Returns:
            str: Localized title for the column.
        """

        return self.title_supplier()

    def get_display_text(self, item: M) -> str:
        """
        Args:
            item (M): Model instance whose display text should be returned.

        Returns:
            str: Display text for the model instance.
        """

        return self.display_text_getter(item)

    def get_sort_key(self, item: M) -> Comparable:
        """
        Args:
            item: Model instance whose sort key should be returned.

        Returns:
            Comparable: Value used for sorting.
        """

        if self.sort_key_getter is not None:
            return self.sort_key_getter(item)

        return self.display_text_getter(item).lower()

    def get_tooltip(self, item: M) -> str:
        """
        Args:
            item (M): Model instance whose tooltip should be returned.

        Returns:
            str: Tooltip text for the model instance.
        """

        if self.tooltip_getter is not None:
            return self.tooltip_getter(item)

        return ""

    def get_icon(self, item: M) -> Optional[QIcon]:
        """
        Args:
            item (M): Model instance whose icon should be returned.

        Returns:
            Optional[QIcon]: Icon for the model instance.
        """

        if self.icon_getter is not None:
            return self.icon_getter(item)

        return None

    def get_foreground_color(self, item: M) -> Optional[Color]:
        """
        Args:
            item (M): Model instance whose foreground color should be returned.

        Returns:
            Optional[Color]: Foreground color for the model instance.
        """

        if self.foreground_color_getter is not None:
            return self.foreground_color_getter(item)

        return None

    def get_font(self, item: M) -> Optional[QFont]:
        """
        Args:
            item (M): Model instance whose font should be returned.

        Returns:
            Optional[QFont]: Font for the model instance.
        """

        if self.font_getter is not None:
            return self.font_getter(item)

        return None

    def get_alignment(self, item: M) -> Qt.AlignmentFlag:
        """
        Args:
            item (M): Model instance whose alignment should be returned.

        Returns:
            Qt.AlignmentFlag: Alignment for the model instance.
        """

        if self.alignment_getter is not None:
            return self.alignment_getter(item)

        return Qt.AlignmentFlag.AlignLeft


class ColumnEnum(Enum):
    """
    Base class for column enums.
    """

    # this constraints subclass members to be of type ColumnConfig
    _value_: ColumnConfig[Any]

    # this is required to satisfy pyright's type checking for the value attribute of the
    # enum members, which is expected to be of type ColumnConfig
    value: ColumnConfig[Any]  # pyright: ignore[reportIncompatibleMethodOverride]

    @classmethod
    def apply_to_tree_widget(cls, tree_widget: QTreeWidget) -> None:
        """
        Applies the column configuration to the given tree widget.
        Columns are ordered by their definition order in the enum.

        Args:
            tree_widget: The tree widget to apply the column configuration to.
        """

        columns: list[ColumnEnum] = [c for c in cls]

        tree_widget.setColumnCount(len(columns))
        tree_widget.setHeaderLabels(
            [column.value.get_title() for column in columns],
        )

        for col in columns:
            if col.value.initial_width is not None:
                tree_widget.setColumnWidth(col.index, col.value.initial_width)

            tree_widget.headerItem().setTextAlignment(
                col.index, col.value.header_alignment
            )

            if col.value.stretch:
                tree_widget.header().setStretchLastSection(False)
                tree_widget.header().setSectionResizeMode(
                    col.index, QHeaderView.ResizeMode.Stretch
                )

    @classmethod
    def column_for_index(cls, index: int) -> Self:
        """
        Args:
            index (int): Zero-based column index.

        Raises:
            IndexError: If the index does not exist.

        Returns:
            Self: Matching column definition.
        """

        return list(cls)[index]

    @property
    def index(self) -> int:
        """The index of the column."""

        return list(type(self)).index(self)

    @classmethod
    def get_columns(cls, model_type: type[M]) -> list[ColumnConfig[M]]:
        """
        Args:
            model_type (type[M]):
                Expected model type. Used to make the expected type explicit at the call
                site. Runtime validation of callable signatures is not possible.

        Returns:
            list[ColumnConfig[M]]: List of column configurations.
        """

        del model_type
        return [cast(ColumnConfig[M], c.value) for c in cls]

    def config_for(self, model_type: type[M]) -> ColumnConfig[M]:
        """
        Args:
            model_type (type[M]):
                Expected model type. Used to make the expected type explicit at the call
                site. Runtime validation of callable signatures is not possible.

        Returns:
            ColumnConfig[M]: Typed column configuration.
        """

        del model_type
        return cast(ColumnConfig[M], self.value)


class TreeItem(QTreeWidgetItem, Generic[M]):
    """
    Tree-widget item backed by a Pydantic model.
    """

    _item: M
    """Model instance represented by the item."""

    _columns: type[ColumnEnum]
    """Enum containing the column definitions."""

    _checkable: bool
    """If the first column contains a checkbox."""

    _cell_values: dict[ColumnEnum, CellValue]
    """Values supplied externally for individual cells."""

    def __init__(
        self, item: M, columns: type[ColumnEnum], checkable: bool = False
    ) -> None:
        """
        Args:
            item (M): Model instance represented by the item.
            columns (type[ColumnEnum]): Enum containing the column definitions.
            checkable (bool): If the first column contains a checkbox.
        """

        super().__init__()

        self._item = item
        self._columns = columns
        self._checkable = checkable
        self._cell_values = {}

        if checkable:
            self.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)

        self.update()

    @property
    def item(self) -> M:
        """The model instance represented by the item."""

        return self._item

    def setValue(self, column: ColumnEnum, value: CellValue) -> None:
        """
        Sets an externally supplied value for a cell.

        Args:
            column (ColumnEnum): Column whose value should be set.
            value (CellValue): Value to display and use for sorting.

        Raises:
            ValueError: If the column does not belong to this item.
        """

        if type(column) is not self._columns:
            raise ValueError("The column does not belong to this tree item.")

        self._cell_values[column] = value
        self.setText(column.index, value.display_text)

    def clearValue(self, column: ColumnEnum) -> None:
        """
        Removes an externally supplied cell value.

        Args:
            column (ColumnEnum): Column whose external value should be removed.

        Raises:
            ValueError: If the column does not belong to this item.
        """

        if type(column) is not self._columns:
            raise ValueError("The column does not belong to this tree item.")

        if column in self._cell_values:
            del self._cell_values[column]
            self.update()

    def update(self) -> None:
        """
        Updates the item according to the current model values.
        """

        for column in self._columns:
            config: ColumnConfig[M] = column.config_for(type(self._item))

            self.setText(column.index, config.get_display_text(self._item))
            self.setToolTip(column.index, config.get_tooltip(self._item))

            icon: Optional[QIcon] = config.get_icon(self._item)
            self.setIcon(column.index, icon if icon is not None else QIcon())

            color: Optional[Color] = config.get_foreground_color(self._item)
            self.setForeground(
                column.index, QBrush(color) if color is not None else QBrush()
            )

            font: Optional[QFont] = config.get_font(self._item)
            self.setFont(column.index, font if font is not None else QFont())

            self.setTextAlignment(column.index, config.get_alignment(self._item))

            cell_value: Optional[CellValue] = self._cell_values.get(column)
            if cell_value is not None:
                self.setText(column.index, cell_value.display_text)

    def setChecked(self, checked: bool) -> None:
        """
        Sets the checked state of the item.

        Args:
            checked (bool): True to check the item, False to uncheck it.
        """

        if not self._checkable:
            raise RuntimeError("Cannot set checked state on a non-checkable item.")

        self.setCheckState(
            0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        )

    def isChecked(self) -> bool:
        """
        Returns whether the item is checked.

        Returns:
            bool: True if the item is checked, False otherwise.
        """

        return self.checkState(0) == Qt.CheckState.Checked

    def _get_sort_key_for_column(self, column: ColumnEnum) -> Comparable:
        """
        Returns the sort key for the given column.

        Args:
            column (ColumnEnum): Column whose sort key should be returned.

        Returns:
            Comparable: Sort key for the column.
        """

        cell_value: Optional[CellValue] = self._cell_values.get(column)
        if cell_value is not None:
            return cell_value.sort_key

        config: ColumnConfig[M] = column.config_for(type(self._item))
        return config.get_sort_key(self._item)

    @override
    def __lt__(self, other: QTreeWidgetItem) -> bool:
        # Qt has a wrong type hint - treeWidget() can indeed be None
        tree_widget = cast(Optional[QTreeWidget], self.treeWidget())
        if tree_widget is None:
            return super().__lt__(other)

        column_index: int = tree_widget.sortColumn()

        if (
            not isinstance(other, TreeItem)
            or other._columns is not self._columns
            or type(other._item) is not type(self._item)
        ):
            # we are intentionally sorting by the displayed text as super().__lt__()
            # somehow leads to an AccessViolation within Qt
            return self.text(column_index) < other.text(column_index)

        other = cast(TreeItem[M], other)

        if column_index < 0:
            # we are intentionally sorting by the displayed text as super().__lt__()
            # somehow leads to an AccessViolation within Qt
            return self.text(column_index) < other.text(column_index)

        column: ColumnEnum = self._columns.column_for_index(column_index)
        return self._get_sort_key_for_column(column) < other._get_sort_key_for_column(
            column
        )
