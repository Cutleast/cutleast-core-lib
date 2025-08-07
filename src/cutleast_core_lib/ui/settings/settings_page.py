"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import Generic, TypeVar, override

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QSpinBox

from core.config.base_config import BaseConfig

from ..widgets.smooth_scroll_area import SmoothScrollArea

T = TypeVar("T", bound=BaseConfig)


class SettingsPage(SmoothScrollArea, Generic[T]):
    """
    Base class for settings pages.
    """

    changed_signal = Signal()
    """This signal gets emitted when a setting is changed."""

    restart_required_signal = Signal()
    """This signal gets emitted when a setting requires a restart."""

    _initial_config: T

    def __init__(self, initial_config: T) -> None:
        super().__init__()

        self._initial_config = initial_config

        self.setObjectName("transparent")

        self._init_ui()

    @abstractmethod
    def _init_ui(self) -> None: ...

    @abstractmethod
    def apply(self, config: T) -> None:
        """
        Applies changes to the config.

        Args:
            config (T): Config to apply changes to
        """

    @abstractmethod
    def validate(self) -> None:
        """
        Validates the user input.

        Raises:
            ConfigValidationError: When the input is invalid.
        """

    @override
    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """
        Event filter to prevent scrolling on spin boxes and comboboxes.

        Install with `QWidget.installEventFilter(self)` on affected widgets.

        Args:
            source (QObject): Event source.
            event (QEvent): Event.

        Returns:
            bool: `True` if the event was handled, `False` otherwise.
        """

        if (
            event.type() == QEvent.Type.Wheel
            and (
                isinstance(source, QComboBox)
                or isinstance(source, QSpinBox)
                or isinstance(source, QDoubleSpinBox)
            )
            and isinstance(event, QWheelEvent)
        ):
            self.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
