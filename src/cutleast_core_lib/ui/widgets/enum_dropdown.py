"""
Copyright (c) Cutleast
"""

from typing import cast, override

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

from cutleast_core_lib.core.utilities.colored_enum import ColoredEnum
from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum

from ..theme.manager import ThemeManager
from ..theme.models.theme import Theme
from .dropdown import Dropdown
from .enum_selector import E, EnumSelector


class EnumDropdown(EnumSelector[E]):
    """
    QComboBox specialized for enums. Has support for localized and colored enums.
    """

    __dropdown: Dropdown

    @override
    def _init_ui(self, initial_value: E) -> QWidget:
        self.__dropdown = Dropdown()

        if issubclass(self._enum_type, LocalizedEnum):
            for i, e in enumerate(self._enum_type):
                self.__dropdown.addItem(e.get_localized_name())
                self.__dropdown.setItemData(
                    i, e.get_localized_description(), role=Qt.ItemDataRole.ToolTipRole
                )

        else:
            for e in self._enum_type:
                self.__dropdown.addItem(e.name)

        self.__apply_item_colors()
        self.setCurrentValue(initial_value)
        self.__update_text_color()

        self.__dropdown.currentTextChanged.connect(
            lambda _: self.currentValueChanged.emit(self.getCurrentValue())
        )
        self.__dropdown.currentIndexChanged.connect(self.__update_text_color)

        if issubclass(self._enum_type, ColoredEnum):
            ThemeManager.get().theme_changed.connect(self.__on_theme_changed)

        return self.__dropdown

    def __apply_item_colors(self) -> None:
        """
        Applies the foreground colors of colored enum members to their items.
        """

        for i, e in enumerate(self._enum_type):
            if isinstance(e, ColoredEnum):
                self.__dropdown.setItemData(
                    i, e.get_fg_color(), role=Qt.ItemDataRole.ForegroundRole
                )

    def __update_text_color(self) -> None:
        """
        Applies the foreground color of the current item to the closed dropdown.
        """

        # QComboBox ignores the ForegroundRole when painting the current item and the
        # application stylesheet overrides palette changes, so a minimal stylesheet
        # is required instead.
        color: object = self.__dropdown.currentData(Qt.ItemDataRole.ForegroundRole)

        if isinstance(color, QColor):
            self.__dropdown.setStyleSheet(
                f"QComboBox:enabled {{ color: rgba({color.red()}, {color.green()}, "
                f"{color.blue()}, {color.alpha()}); }}"
            )
        else:
            self.__dropdown.setStyleSheet("")

    def __on_theme_changed(self, theme: Theme) -> None:
        """
        Reapplies the item colors since they depend on the current theme.

        Args:
            theme (Theme): The new theme.
        """

        self.__apply_item_colors()
        self.__update_text_color()

    @override
    def getCurrentValue(self) -> E:
        if issubclass(self._enum_type, LocalizedEnum):
            return cast(
                E, self._enum_type.get_by_localized_name(self.__dropdown.currentText())
            )
        else:
            return self._enum_type[self.__dropdown.currentText()]

    @override
    def setCurrentValue(self, value: E) -> None:
        if isinstance(value, LocalizedEnum):
            self.__dropdown.setCurrentText(value.get_localized_name())
        else:
            self.__dropdown.setCurrentText(value.name)

    def setCurrentIndex(self, index: int) -> None:
        """
        Sets the current selected index.

        Args:
            index (int): The index to set as the current selection.
        """

        self.__dropdown.setCurrentIndex(index)
