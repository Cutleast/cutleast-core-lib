"""
Copyright (c) Cutleast
"""

import re
from abc import ABCMeta, abstractmethod
from typing import override

from PySide6.QtGui import QColor, QPalette

from .icon_provider import IconProvider
from .theme import UiTheme
from .theme_manager import ThemeManager as BaseThemeManager


class UiThemeManager(BaseThemeManager, metaclass=ABCMeta):
    """
    ThemeManager implementation for the UiTheme model.
    """

    PLACEHOLDER_PATTERN: str = r"@(?P<key>[a-zA-Z0-9_-]+)"
    """Regex pattern for theme placeholders in the raw stylesheet."""

    _theme: UiTheme

    @override
    def _init(self) -> None:
        raw_theme_json: str = self._get_raw_theme_string()
        self._theme = UiTheme.model_validate_json(raw_theme_json)
        self._theme.base_accent_color = self._accent_color

        super()._init()

    @abstractmethod
    def _get_raw_theme_string(self) -> str:
        """
        Gets the raw JSON string for the UI theme.

        Returns:
            str: The raw JSON string.
        """

    @abstractmethod
    def _get_raw_stylesheet(self) -> str:
        """
        Gets the raw stylesheet.

        Returns:
            str: The raw stylesheet.
        """

    @override
    def _get_stylesheet(self) -> str:
        placeholders: dict[str, str] = self._theme.placeholder_dict
        placeholder_pattern: re.Pattern[str] = re.compile(
            UiThemeManager.PLACEHOLDER_PATTERN
        )

        raw_stylesheet: str = self._get_raw_stylesheet()
        final_stylesheet: str = placeholder_pattern.sub(
            lambda match: placeholders[match.group("key")], raw_stylesheet
        )

        return final_stylesheet

    @override
    def _apply_to_palette(self, palette: QPalette) -> None:
        # Window / Base backgrounds
        palette.setColor(
            QPalette.ColorRole.Window, QColor(self._theme.primary_bg_color)
        )
        palette.setColor(
            QPalette.ColorRole.Button, QColor(self._theme.secondary_bg_color)
        )
        palette.setColor(
            QPalette.ColorRole.Base, QColor(self._theme.secondary_bg_color)
        )
        palette.setColor(
            QPalette.ColorRole.AlternateBase, QColor(self._theme.tertiary_bg_color)
        )

        # Text
        palette.setColor(
            QPalette.ColorRole.WindowText, QColor(self._theme.primary_fg_color)
        )
        palette.setColor(QPalette.ColorRole.Text, QColor(self._theme.primary_fg_color))
        palette.setColor(
            QPalette.ColorRole.ButtonText, QColor(self._theme.primary_fg_color)
        )
        palette.setColor(
            QPalette.ColorRole.PlaceholderText, QColor(self._theme.placeholder_fg_color)
        )

        # Disabled text
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.WindowText,
            QColor(self._theme.disabled_fg_color),
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            QColor(self._theme.disabled_fg_color),
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            QColor(self._theme.disabled_fg_color),
        )

        # Accent color
        if self._theme.has_accent_color:
            palette.setColor(
                QPalette.ColorRole.Accent, QColor(self._theme.primary_accent_color)
            )
            palette.setColor(
                QPalette.ColorRole.Link, QColor(self._theme.primary_accent_color)
            )
            palette.setColor(
                QPalette.ColorRole.LinkVisited, QColor(self._theme.hover_accent_color)
            )

            # Selection / Highlight
            palette.setColor(
                QPalette.ColorRole.Highlight, QColor(self._theme.hover_accent_color)
            )
            palette.setColor(
                QPalette.ColorRole.HighlightedText, QColor(self._theme.accent_fg_color)
            )

        # Tooltips & Menus
        palette.setColor(
            QPalette.ColorRole.ToolTipBase, QColor(self._theme.popup_bg_color)
        )
        palette.setColor(
            QPalette.ColorRole.ToolTipText, QColor(self._theme.popup_fg_color)
        )

        # Borders / Lines
        palette.setColor(QPalette.ColorRole.Shadow, QColor(self._theme.border_color))
        palette.setColor(QPalette.ColorRole.Mid, QColor(self._theme.border_color))
        palette.setColor(QPalette.ColorRole.Midlight, QColor(self._theme.border_color))

        # Disabled border
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Shadow,
            QColor(self._theme.disabled_border_color),
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Mid,
            QColor(self._theme.disabled_border_color),
        )
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Midlight,
            QColor(self._theme.disabled_border_color),
        )

    @override
    def _init_icon_provider(self) -> IconProvider:
        return IconProvider(self.ui_mode, self._theme.primary_fg_color)

    def get_theme(self) -> UiTheme:
        """
        Gets the current UI theme.

        Returns:
            UiTheme: The current UI theme.
        """

        return self._theme
