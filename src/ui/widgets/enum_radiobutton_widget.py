"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QRadioButton, QVBoxLayout, QWidget

from core.utilities.localized_enum import LocalizedEnum

from .enum_selector import E, EnumSelector


class EnumRadiobuttonsWidget(EnumSelector[E]):
    """
    A widget with radio buttons for selecting an enum value.
    """

    __orientation: Qt.Orientation

    __layout: QVBoxLayout | QHBoxLayout
    __enum_items: dict[E, QRadioButton]

    def __init__(
        self,
        enum_type: type[E],
        initial_value: Optional[E] = None,
        orientation: Qt.Orientation = Qt.Orientation.Vertical,
    ) -> None:
        """
        Args:
            enum_type (type[E]): Type of the enum.
            initial_value (Optional[E], optional):
                Initial enum member to select. Defaults to the first enum member.
            orientation (Qt.Orientation, optional):
                Layout orientation. Defaults to Qt.Orientation.Vertical.
        """

        self.__orientation = orientation

        super().__init__(enum_type, initial_value)

    @override
    def _init_ui(self, initial_value: E) -> QWidget:
        widget = QWidget()

        if self.__orientation == Qt.Orientation.Horizontal:
            self.__layout = QHBoxLayout()
        else:
            self.__layout = QVBoxLayout()

        self.__layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(self.__layout)

        self.__init_radiobuttons()

        self.setCurrentValue(initial_value)

        for radiobutton in self.__enum_items.values():
            radiobutton.toggled.connect(
                lambda _: self.currentValueChanged.emit(self.getCurrentValue())
            )

        return widget

    def __init_radiobuttons(self) -> None:
        self.__enum_items = {}

        if issubclass(self._enum_type, LocalizedEnum):
            for enum_value in self._enum_type:
                radio_button = QRadioButton(enum_value.get_localized_name())
                radio_button.setToolTip(enum_value.get_localized_description())
                self.__enum_items[enum_value] = radio_button
                self.__layout.addWidget(radio_button)
        else:
            for enum_value in self._enum_type:
                radio_button = QRadioButton(enum_value.name)
                radio_button.setToolTip(enum_value.__doc__ or "")
                self.__enum_items[enum_value] = radio_button
                self.__layout.addWidget(radio_button)

    @override
    def getCurrentValue(self) -> E:
        for enum_value, radiobutton in self.__enum_items.items():
            if radiobutton.isChecked():
                return enum_value

        raise ValueError("No radio button is checked")

    @override
    def setCurrentValue(self, value: E) -> None:
        self.__enum_items[value].setChecked(True)
