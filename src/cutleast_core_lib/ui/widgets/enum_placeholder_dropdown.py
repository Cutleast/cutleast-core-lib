"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Generic, Optional, TypeVar, cast

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from cutleast_core_lib.core.utilities.colored_enum import ColoredEnum
from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum

from ..theme.manager import ThemeManager
from ..theme.models.theme import Theme
from .placeholder_dropdown import PlaceholderDropdown

E = TypeVar("E", bound="Enum")


class EnumPlaceholderDropdown(PlaceholderDropdown, Generic[E]):
    """
    PlaceholderDropdown specialized for enums. Has support for localized and colored
    enums.
    """

    currentValueChanged = Signal(Enum)
    """
    This signal gets emitted when the selected enum value changes.

    Args:
        Optional[E]: The selected enum value or None
    """

    __enum_type: type[E]

    def __init__(
        self,
        enum_type: type[E],
        initial_value: Optional[E] = None,
        placeholder_text: Optional[str] = None,
    ) -> None:
        """
        Args:
            enum_type (type[E]): The enum type.
            initial_value (Optional[E], optional): The initial enum value. Defaults to None.
            placeholder_text (Optional[str], optional): The placeholder text. Defaults to None.
        """

        super().__init__(placeholder_text=placeholder_text)

        self.__enum_type = enum_type

        if issubclass(enum_type, LocalizedEnum):
            for i, e in enumerate(enum_type):
                self.addItem(e.get_localized_name())
                self.setItemData(
                    i + 1,  # add 1 to account for placeholder
                    e.get_localized_description(),
                    role=Qt.ItemDataRole.ToolTipRole,
                )

        else:
            for e in enum_type:
                self.addItem(e.name)

        self.__apply_item_colors()

        if initial_value is not None:
            if isinstance(initial_value, LocalizedEnum):
                self.setCurrentText(initial_value.get_localized_name())
            else:
                self.setCurrentText(initial_value.name)
        else:
            self.setCurrentIndex(-1)

        self.__update_text_color()

        self.currentTextChanged.connect(
            lambda _: self.currentValueChanged.emit(self.getCurrentValue())
        )
        self.currentIndexChanged.connect(self.__update_text_color)

        if issubclass(enum_type, ColoredEnum):
            ThemeManager.get().theme_changed.connect(self.__on_theme_changed)

    def __apply_item_colors(self) -> None:
        """
        Applies the foreground colors of colored enum members to their items.
        """

        for i, e in enumerate(self.__enum_type):
            if isinstance(e, ColoredEnum):
                self.setItemData(
                    i + 1,  # add 1 to account for placeholder
                    e.get_fg_color(),
                    role=Qt.ItemDataRole.ForegroundRole,
                )

    def __update_text_color(self) -> None:
        """
        Applies the foreground color of the current item to the closed dropdown.
        """

        # QComboBox ignores the ForegroundRole when painting the current item and the
        # application stylesheet overrides palette changes, so a minimal stylesheet
        # is required instead.
        color: object = self.currentData(Qt.ItemDataRole.ForegroundRole)

        if isinstance(color, QColor):
            self.setStyleSheet(
                f"QComboBox:enabled {{ color: rgba({color.red()}, {color.green()}, "
                f"{color.blue()}, {color.alpha()}); }}"
            )
        else:
            self.setStyleSheet("")

    def __on_theme_changed(self, theme: Theme) -> None:
        """
        Reapplies the item colors since they depend on the current theme.

        Args:
            theme (Theme): The new theme.
        """

        self.__apply_item_colors()
        self.__update_text_color()

    def getCurrentValue(self) -> Optional[E]:
        """
        Returns:
            Optional[E]:
                The currently selected enum member or None if placeholder is selected.
        """

        if self.currentIndex() == -1:
            return None
        elif issubclass(self.__enum_type, LocalizedEnum):
            return cast(E, self.__enum_type.get_by_localized_name(self.currentText()))
        else:
            return self.__enum_type[self.currentText()]

    def setCurrentValue(self, value: Optional[E]) -> None:
        """
        Sets the specified enum value as the currently selected.

        Args:
            value (Optional[E]): Enum value to select
        """

        if isinstance(value, LocalizedEnum):
            self.setCurrentText(value.get_localized_name())
        elif value is not None:
            self.setCurrentText(value.name)
        else:
            self.setCurrentIndex(-1)
