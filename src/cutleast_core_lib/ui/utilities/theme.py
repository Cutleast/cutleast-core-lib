"""
Copyright (c) Cutleast
"""

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, BeforeValidator, Field
from PySide6.QtGui import QColor

from cutleast_core_lib.core.config.validation_utils import ValidationUtils

from .ui_mode import UIMode

HexColorStr = Annotated[str, BeforeValidator(ValidationUtils.validate_hex_color)]


class UiTheme(BaseModel):
    """
    Complete UI theme model for Qt-based desktop applications. Provides all color tokens
    needed for a consistent QPalette. Accent color derives from a base color and adapts
    to UI mode.
    """

    ui_mode: Annotated[
        Literal[UIMode.Dark, UIMode.Light], BeforeValidator(lambda v: UIMode(v))
    ]
    """UI mode the theme belongs to."""

    # Fonts
    title_font: str
    """Font used for headings and prominent labels."""

    primary_font: str
    """Primary text font used across the UI."""

    monospace_font: str
    """Monospace font used for code-like or technical elements."""

    # Backgrounds
    primary_bg_color: HexColorStr
    """Primary window background."""

    secondary_bg_color: HexColorStr
    """Background for widgets, panels, buttons."""

    tertiary_bg_color: HexColorStr
    """Nested surface background for subtle hierarchy."""

    hover_bg_color: HexColorStr
    """Background for hovered elements."""

    active_bg_color: HexColorStr
    """Background for active/pressed/focused input fields or buttons."""

    highlighted_bg_color: HexColorStr
    """Used for general emphasis or highlight backgrounds."""

    disabled_bg_color: HexColorStr
    """Background for disabled elements."""

    # Text
    primary_fg_color: HexColorStr
    """Primary text color."""

    secondary_fg_color: HexColorStr
    """Secondary text color, e.g. for hints and low-emphasis text."""

    disabled_fg_color: HexColorStr
    """Foreground color of disabled text."""

    placeholder_fg_color: HexColorStr
    """Placeholder text color for input fields."""

    # Borders / Lines
    border_color: HexColorStr
    """Generic border color for frames, inputs, separators."""

    disabled_border_color: HexColorStr
    """Border color for disabled widgets."""

    # Tooltips & Menus
    popup_bg_color: HexColorStr
    """Tooltip & menu background color."""

    popup_fg_color: HexColorStr
    """Tooltip & menu foreground color."""

    # Accent
    alt_accent_fg_color: HexColorStr
    """
    Alternate accent foreground for cases where the accent background is too dark or too
    light for the primary text color.
    """

    base_accent_color: Optional[HexColorStr] = Field(None, exclude=True)
    """Base accent color set by the user. All accent variants derive from it."""

    @property
    def has_accent_color(self) -> bool:
        """Indicates whether an accent color has been provided."""

        return self.base_accent_color is not None

    @property
    def primary_accent_color(self) -> HexColorStr:
        """
        Main accent color. Desaturated in dark mode to avoid visual noise. Used for
        primary actions, checkbox/radio/slider highlights.

        Raises:
            ValueError: When no accent color is defined.
        """

        if self.base_accent_color is None:
            raise ValueError("No accent color defined.")

        base_color = QColor(self.base_accent_color)

        accent_color: QColor
        if self.ui_mode == UIMode.Light:
            accent_color = base_color
        else:
            accent_color = base_color.toHsv()
            accent_color.setHsv(
                accent_color.hue(),
                int(accent_color.saturation() * 0.7),
                accent_color.value(),
            )

        return accent_color.name(QColor.NameFormat.HexRgb)

    @property
    def hover_accent_color(self) -> HexColorStr:
        """
        Hover color for accent elements:

        - **Light mode:** Darker accent.
        - **Dark mode:** Lighter accent.

        Raises:
            ValueError: When no accent color is defined.
        """

        base_color = QColor(self.primary_accent_color)

        modified: QColor
        if self.ui_mode == UIMode.Light:
            modified = base_color.darker(120)
        else:
            modified = base_color.lighter(120)

        return modified.name(QColor.NameFormat.HexRgb)

    @property
    def accent_fg_color(self) -> HexColorStr:
        """
        Foreground color automatically chosen to contrast well with primary accent color.

        Raises:
            ValueError: When no accent color is defined.
        """

        base_color = QColor(self.primary_accent_color)

        # Choose contrast color based on luminance and UI mode.
        accent_fg_color: HexColorStr
        if (self.ui_mode == UIMode.Light and base_color.lightness() < 128) or (
            self.ui_mode == UIMode.Dark and base_color.lightness() >= 128
        ):
            accent_fg_color = self.alt_accent_fg_color
        else:
            accent_fg_color = self.primary_fg_color

        return accent_fg_color

    @property
    def accent_fg_ui_mode(self) -> Literal[UIMode.Dark, UIMode.Light]:
        """
        UI mode for the foreground of accent elements.

        Raises:
            ValueError: When no accent color is defined.
        """

        accent_color = QColor(self.primary_accent_color)

        if accent_color.lightness() < 128:
            return UIMode.Dark  # = light icons
        else:
            return UIMode.Light  # = dark icons

    @property
    def disabled_accent_color(self) -> HexColorStr:
        """
        The accent color with saturation = 0 for disabled elements.

        Raises:
            ValueError: When no accent color is defined.
        """

        if self.base_accent_color is None:
            raise ValueError("No accent color defined.")

        base_color = QColor(self.base_accent_color)

        modified: QColor = base_color.toHsv()
        modified.setHsv(modified.hue(), 0, modified.value())

        return modified.name(QColor.NameFormat.HexRgb)

    @property
    def placeholder_dict(self) -> dict[str, str]:
        """
        A dictionary mapping placeholder keys to their corresponding theme values.
        """

        data: dict[str, str] = self.model_dump()
        data["ui_mode"] = self.ui_mode.value.lower()

        if self.has_accent_color:
            data.update(
                {
                    "primary_accent_color": self.primary_accent_color,
                    "hover_accent_color": self.hover_accent_color,
                    "accent_fg_color": self.accent_fg_color,
                    "accent_fg_ui_mode": self.accent_fg_ui_mode.value.lower(),
                    "disabled_accent_color": self.disabled_accent_color,
                }
            )

        return data
