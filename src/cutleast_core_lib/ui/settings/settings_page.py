"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import Generic, TypeVar, override

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QSpinBox

from cutleast_core_lib.core.config.base_config import BaseConfig
from cutleast_core_lib.core.config.manager import ConfigManager

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

    theme_update_required_signal = Signal()
    """This signal gets emitted when a setting requires a theme update."""

    _config_manager: ConfigManager[T]
    _config: T

    def __init__(self, config_manager: ConfigManager[T]) -> None:
        """
        Args:
            config_manager (ConfigManager[T]):
                The manager for the config that is represented by this page.
        """

        super().__init__()

        self._config_manager = config_manager
        self._config = config_manager.config

        self._init_ui()

    @abstractmethod
    def _init_ui(self) -> None: ...

    @abstractmethod
    def apply(self) -> None:
        """
        Applies changes to the config.
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
            and isinstance(source, (QComboBox, QSpinBox, QDoubleSpinBox))
            and isinstance(event, QWheelEvent)
        ):
            self.wheelEvent(event)
            return True

        return super().eventFilter(source, event)
