"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum


class UiMode(LocalizedEnum):
    """
    Enum for UI modes (Dark, Light, System)
    """

    Dark = "Dark"
    Light = "Light"
    System = "System"

    @override
    def get_localized_name(self) -> str:
        match self:
            case UiMode.Dark:
                return QApplication.translate("UiMode", "Dark")
            case UiMode.Light:
                return QApplication.translate("UiMode", "Light")
            case UiMode.System:
                return QApplication.translate("UiMode", "System")

    @classmethod
    def from_qt_color_scheme(cls, scheme: Qt.ColorScheme) -> UiMode:
        """
        Converts a Qt.ColorScheme to a UiMode.

        Args:
            scheme (Qt.ColorScheme): The Qt color scheme.

        Returns:
            UiMode: The corresponding UiMode.
        """

        match scheme:
            case Qt.ColorScheme.Dark:
                return UiMode.Dark
            case Qt.ColorScheme.Light:
                return UiMode.Light
            case Qt.ColorScheme.Unknown:
                return UiMode.System

    def to_qt_color_scheme(self) -> Qt.ColorScheme:
        """
        Returns:
            Qt.ColorScheme: The corresponding Qt color scheme.
        """

        match self:
            case UiMode.Dark:
                return Qt.ColorScheme.Dark
            case UiMode.Light:
                return Qt.ColorScheme.Light
            case UiMode.System:
                return Qt.ColorScheme.Unknown
