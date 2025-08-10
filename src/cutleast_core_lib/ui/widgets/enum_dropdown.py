"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum

from .dropdown import Dropdown
from .enum_selector import E, EnumSelector


class EnumDropdown(EnumSelector[E]):
    """
    QComboBox specialized for enums. Has support for localized enums.
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

        self.setCurrentValue(initial_value)

        self.__dropdown.currentTextChanged.connect(
            lambda _: self.currentValueChanged.emit(self.getCurrentValue())
        )

        return self.__dropdown

    @override
    def getCurrentValue(self) -> E:
        if issubclass(self._enum_type, LocalizedEnum):
            return self._enum_type.get_by_localized_name(self.__dropdown.currentText())
        else:
            return self._enum_type[self.__dropdown.currentText()]

    @override
    def setCurrentValue(self, value: E) -> None:
        if isinstance(value, LocalizedEnum):
            self.__dropdown.setCurrentText(value.get_localized_name())
        else:
            self.__dropdown.setCurrentText(value.name)
