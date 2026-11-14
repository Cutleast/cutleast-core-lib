"""
Copyright (c) Cutleast
"""

import time
from typing import override

from pydantic import BaseModel, Field
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import QApplication

from cutleast_core_lib.core.utilities.colored_enum import ColoredEnum
from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.theme.models.theme import Theme
from cutleast_core_lib.ui.theme.models.types import ThemeAlias
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider


class Alert(BaseModel, frozen=True):
    """
    An alert represents a warning, error or critical issue that should be shown to the
    user.
    """

    timestamp: int = Field(default_factory=lambda: int(time.time()))
    """The UNIX timestamp of the alert."""

    class Severity(int, LocalizedEnum, ColoredEnum):
        """The severity of an alert."""

        Notice = 1
        """The item could have some minor issues that should be looked at."""

        Warning = 2
        """The item has some issues that should be looked at."""

        Error = 3
        """The item has some major issues that should definitely be fixed."""

        @override
        def get_localized_name(self) -> str:
            match self:
                case Alert.Severity.Notice:
                    return QApplication.translate("Alert.Severity", "Notice")
                case Alert.Severity.Warning:
                    return QApplication.translate("Alert.Severity", "Warning")
                case Alert.Severity.Error:
                    return QApplication.translate("Alert.Severity", "Error")

        @override
        def get_localized_description(self) -> str:
            match self:
                case Alert.Severity.Notice:
                    return QApplication.translate(
                        "Alert.Severity",
                        "The alert could be about some minor issue that should be "
                        "looked at.",
                    )
                case Alert.Severity.Warning:
                    return QApplication.translate(
                        "Alert.Severity",
                        "The alert is some issue that should be looked at.",
                    )
                case Alert.Severity.Error:
                    return QApplication.translate(
                        "Alert.Severity",
                        "The alert is a major issue that should definitely be fixed.",
                    )

        @override
        def get_base_color(self) -> QColor:
            theme: Theme = ThemeManager.get().theme

            token: ThemeAlias
            match self:
                case Alert.Severity.Notice:
                    token = theme.colors.information
                case Alert.Severity.Warning:
                    token = theme.colors.warning
                case Alert.Severity.Error:
                    token = theme.colors.error

            return QColor.fromString(theme.resolve(token))

        @override
        def get_bg_color(self) -> QColor:
            theme: Theme = ThemeManager.get().theme

            token: ThemeAlias
            match self:
                case Alert.Severity.Notice:
                    token = theme.colors.information_bg
                case Alert.Severity.Warning:
                    token = theme.colors.warning_bg
                case Alert.Severity.Error:
                    token = theme.colors.error_bg

            return QColor.fromString(theme.resolve(token))

        @override
        def get_highlighted_bg_color(self) -> QColor:
            theme: Theme = ThemeManager.get().theme

            token: ThemeAlias
            match self:
                case Alert.Severity.Notice:
                    token = theme.colors.information_bg_hover
                case Alert.Severity.Warning:
                    token = theme.colors.warning_bg_hover
                case Alert.Severity.Error:
                    token = theme.colors.error_bg_hover

            return QColor.fromString(theme.resolve(token))

        @override
        def get_fg_color(self) -> QColor:
            theme: Theme = ThemeManager.get().theme

            token: ThemeAlias
            match self:
                case Alert.Severity.Notice:
                    token = theme.colors.information_fg
                case Alert.Severity.Warning:
                    token = theme.colors.warning_fg
                case Alert.Severity.Error:
                    token = theme.colors.error_fg

            return QColor.fromString(theme.resolve(token))

        def get_icon(self) -> QIcon:
            """
            Returns:
                QIcon: An icon for this severity in the severity's foreground color.
            """

            icon: QIcon
            match self:
                case Alert.Severity.Notice:
                    icon = IconProvider.get_qta_icon(
                        "mdi6.information-outline",
                        color=IconProvider.Color.Information,
                        color_active=IconProvider.Color.Information,
                        color_selected=IconProvider.Color.Information,
                        color_on=IconProvider.Color.Information,
                    )
                case Alert.Severity.Warning:
                    icon = IconProvider.get_qta_icon(
                        "mdi6.alert-outline",
                        color=IconProvider.Color.Warning,
                        color_active=IconProvider.Color.Warning,
                        color_selected=IconProvider.Color.Warning,
                        color_on=IconProvider.Color.Warning,
                    )
                case Alert.Severity.Error:
                    icon = IconProvider.get_qta_icon(
                        "mdi6.alert-octagon-outline",
                        color=IconProvider.Color.Error,
                        color_active=IconProvider.Color.Error,
                        color_selected=IconProvider.Color.Error,
                        color_on=IconProvider.Color.Error,
                    )

            return icon

    severity: Severity
    """The severity of the alert."""

    title: str
    """The (localized) title of the alert."""

    summary: str = ""
    """A short (localized) summary of the alert."""

    details: str = ""
    """A traceback or similar."""

    context: dict[str, str] = Field(default_factory=dict)
    """Additional context in the form of localized property names and values."""

    @override
    def __hash__(self) -> int:
        return hash(self.model_dump_json())
