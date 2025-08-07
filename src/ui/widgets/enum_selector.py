"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from enum import Enum
from typing import Generic, Optional, TypeVar

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

E = TypeVar("E", bound=Enum)


class EnumSelector(QWidget, Generic[E]):
    """
    Base class for widgets that allow the selection of an enum member.
    """

    currentValueChanged = Signal(Enum)
    """
    This signal gets emitted when the selected enum member changes.

    Args:
        E: The selected enum member.
    """

    _enum_type: type[E]

    def __init__(self, enum_type: type[E], initial_value: Optional[E] = None) -> None:
        """
        Args:
            enum_type (type[E]): Type of the enum.
            initial_value (Optional[E], optional):
                Initial enum member to select. Defaults to the first enum member.
        """

        super().__init__()

        self._enum_type = enum_type

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vlayout)
        self.setContentsMargins(0, 0, 0, 0)
        self.setObjectName("transparent")

        vlayout.addWidget(
            self._init_ui(initial_value or list(enum_type.__members__.values())[0])
        )

    @abstractmethod
    def _init_ui(self, initial_value: E) -> QWidget:
        """
        Initializes the UI.

        Args:
            initial_value (E): The initial enum member to select.

        Returns:
            QWidget: The initialized UI.
        """

    @abstractmethod
    def getCurrentValue(self) -> E:
        """
        Returns:
            E: The currently selected enum member.
        """

    @abstractmethod
    def setCurrentValue(self, value: E) -> None:
        """
        Sets the specified enum value as the currently selected.

        Args:
            value (E): Enum member to select.
        """
