"""
Copyright (c) Cutleast
"""

import re
from typing import Optional, Self

from PySide6.QtGui import QColor, QPalette

from ..utils import resolve_attr_reference
from .definition import ThemeDefinition
from .palette import ColorPalette
from .types import TOKEN_GROUP_KEY, TOKEN_PATTERN, HexColorStr, TokenRef


class Theme(ThemeDefinition):
    """
    Immutable model for a complete theme, including colors, fonts and metrics.
    """

    primary_palette: ColorPalette
    """Primary color palette."""

    error_palette: ColorPalette
    """Error color palette."""

    caution_palette: ColorPalette
    """Caution color palette."""

    warning_palette: ColorPalette
    """Warning color palette."""

    success_palette: ColorPalette
    """Success color palette."""

    information_palette: ColorPalette
    """Information color palette."""

    @classmethod
    def from_definition(
        cls, definition: ThemeDefinition, primary_color: HexColorStr
    ) -> Self:
        """
        Combines a raw theme definition with a primary color to create a complete theme.

        Args:
            definition (ThemeDefinition): The raw theme definition.
            primary_color (HexColorStr): The primary color to use for the theme.

        Returns:
            Self: An instance of the Theme class with the primary color applied.
        """

        return cls(
            **definition.model_dump(),
            primary_palette=ColorPalette.from_seed_color(
                primary_color, definition.ui_mode
            ),
            error_palette=ColorPalette.from_seed_color(
                definition.error_color, definition.ui_mode
            ),
            caution_palette=ColorPalette.from_seed_color(
                definition.caution_color, definition.ui_mode
            ),
            warning_palette=ColorPalette.from_seed_color(
                definition.warning_color, definition.ui_mode
            ),
            success_palette=ColorPalette.from_seed_color(
                definition.success_color, definition.ui_mode
            ),
            information_palette=ColorPalette.from_seed_color(
                definition.information_color, definition.ui_mode
            ),
        )

    def resolve(self, token: str | TokenRef) -> str:
        """
        Resolves a token reference to its actual value.

        Args:
            token (str | TokenRef): The token reference to resolve.

        Returns:
            str: The resolved token value.
        """

        token_match: Optional[re.Match[str]] = TOKEN_PATTERN.fullmatch(token)
        if token_match is None:
            return token  # not a token

        return str(resolve_attr_reference(self, token, TOKEN_PATTERN, TOKEN_GROUP_KEY))

    def to_qpalette(self, qpalette: QPalette) -> QPalette:
        """
        Applies the theme's colors to a QPalette.

        Args:
            qpalette (QPalette): The QPalette to apply the theme to.

        Returns:
            QPalette: The modified QPalette with the theme's colors applied.
        """

        # Window / Base backgrounds
        qpalette.setColor(
            QPalette.ColorRole.Window, QColor(self.resolve(self.colors.bg_base))
        )
        qpalette.setColor(
            QPalette.ColorRole.Button, QColor(self.resolve(self.colors.surface))
        )
        qpalette.setColor(
            QPalette.ColorRole.Base, QColor(self.resolve(self.colors.bg_base))
        )
        qpalette.setColor(
            QPalette.ColorRole.AlternateBase,
            QColor(self.resolve(self.colors.bg_elevated)),
        )

        # Text
        qpalette.setColor(
            QPalette.ColorRole.WindowText, QColor(self.resolve(self.texts.text.color))
        )
        qpalette.setColor(
            QPalette.ColorRole.Text, QColor(self.resolve(self.texts.text.color))
        )
        qpalette.setColor(
            QPalette.ColorRole.ButtonText, QColor(self.resolve(self.texts.text.color))
        )
        qpalette.setColor(
            QPalette.ColorRole.PlaceholderText,
            QColor(self.resolve(self.texts.secondary.color)),
        )

        # Disabled text
        qpalette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.WindowText,
            QColor(self.resolve(self.texts.secondary.color)),
        )
        qpalette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Text,
            QColor(self.resolve(self.texts.secondary.color)),
        )
        qpalette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
            QColor(self.resolve(self.texts.secondary.color)),
        )

        # Accent color
        qpalette.setColor(
            QPalette.ColorRole.Accent, QColor(self.resolve(self.colors.primary_fg))
        )
        qpalette.setColor(
            QPalette.ColorRole.Link, QColor(self.resolve(self.colors.primary_fg))
        )
        qpalette.setColor(
            QPalette.ColorRole.LinkVisited,
            QColor(self.resolve(self.colors.primary_fg)),
        )

        # Selection / Highlight
        qpalette.setColor(
            QPalette.ColorRole.Highlight,
            QColor(self.resolve(self.colors.primary_bg_hover)),
        )
        qpalette.setColor(
            QPalette.ColorRole.HighlightedText,
            QColor(self.resolve(self.texts.text.color)),
        )

        # Tooltips & Menus
        qpalette.setColor(
            QPalette.ColorRole.ToolTipBase, QColor(self.resolve(self.colors.bg_base))
        )
        qpalette.setColor(
            QPalette.ColorRole.ToolTipText, QColor(self.resolve(self.texts.text.color))
        )

        # Borders / Lines
        qpalette.setColor(
            QPalette.ColorRole.Shadow, QColor(self.resolve(self.colors.border))
        )
        qpalette.setColor(
            QPalette.ColorRole.Mid, QColor(self.resolve(self.colors.border))
        )
        qpalette.setColor(
            QPalette.ColorRole.Midlight, QColor(self.resolve(self.colors.border))
        )

        # Disabled border
        qpalette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Shadow,
            QColor(self.resolve(self.colors.border)),
        )
        qpalette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Mid,
            QColor(self.resolve(self.colors.border)),
        )
        qpalette.setColor(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Midlight,
            QColor(self.resolve(self.colors.border)),
        )

        return qpalette
