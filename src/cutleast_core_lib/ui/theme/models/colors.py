"""
Copyright (c) Cutleast
"""

from .base import ThemeModel
from .types import ThemeAlias


class ColorAliases(ThemeModel):
    """
    Theme aliases for semantic colors.
    """

    # Background colors

    bg_base: ThemeAlias
    """Used for the main application background and non-elevated areas."""

    bg_subtle: ThemeAlias
    """Used for slightly differentiated background areas."""

    bg_elevated: ThemeAlias
    """Used for elevated surfaces such as toolbars, panels and cards."""

    # Surface colors

    surface: ThemeAlias
    """Used for regular interactive control surfaces."""

    surface_hover: ThemeAlias
    """Used for interactive control surfaces while hovered."""

    surface_pressed: ThemeAlias
    """Used for interactive control surfaces while pressed."""

    surface_selected: ThemeAlias
    """Used for selected items and controls."""

    surface_disabled: ThemeAlias
    """Used for disabled control surfaces."""

    # Border colors

    border: ThemeAlias
    """Used for borders, separators, and other subtle visual boundaries."""

    border_strong: ThemeAlias
    """Used for boundaries that require stronger visual emphasis."""

    # Effect colors

    shadow: ThemeAlias
    """Used for drop shadows cast by elevated transient surfaces."""

    # Primary colors

    primary: ThemeAlias
    """Used as the primary accent color and for emphasized controls."""

    primary_fg: ThemeAlias
    """Used for primary-colored texts and icons."""

    primary_bg: ThemeAlias
    """Used for subtle primary-colored backgrounds and selections."""

    primary_bg_hover: ThemeAlias
    """Used for primary-colored controls while hovered."""

    primary_bg_pressed: ThemeAlias
    """Used for primary-colored controls while pressed."""

    primary_bg_disabled: ThemeAlias
    """Used for disabled primary-colored controls."""

    # Status colors

    error: ThemeAlias
    """Used as the error accent color."""

    error_fg: ThemeAlias
    """Used for error-colored texts and icons."""

    error_bg: ThemeAlias
    """Used for subtle error-colored backgrounds and selections."""

    error_bg_hover: ThemeAlias
    """Used for error-colored controls while hovered."""

    error_bg_pressed: ThemeAlias
    """Used for error-colored controls while pressed."""

    error_bg_disabled: ThemeAlias
    """Used for disabled error-colored controls."""

    caution: ThemeAlias
    """Used as the caution accent color."""

    caution_fg: ThemeAlias
    """Used for caution-colored texts and icons."""

    caution_bg: ThemeAlias
    """Used for subtle caution-colored backgrounds and selections."""

    caution_bg_hover: ThemeAlias
    """Used for caution-colored controls while hovered."""

    caution_bg_pressed: ThemeAlias
    """Used for caution-colored controls while pressed."""

    caution_bg_disabled: ThemeAlias
    """Used for disabled caution-colored controls."""

    warning: ThemeAlias
    """Used as the warning accent color."""

    warning_fg: ThemeAlias
    """Used for warning-colored texts and icons."""

    warning_bg: ThemeAlias
    """Used for subtle warning-colored backgrounds and selections."""

    warning_bg_hover: ThemeAlias
    """Used for warning-colored controls while hovered."""

    warning_bg_pressed: ThemeAlias
    """Used for warning-colored controls while pressed."""

    warning_bg_disabled: ThemeAlias
    """Used for disabled warning-colored controls."""

    success: ThemeAlias
    """Used as the success accent color."""

    success_fg: ThemeAlias
    """Used for success-colored texts and icons."""

    success_bg: ThemeAlias
    """Used for subtle success-colored backgrounds and selections."""

    success_bg_hover: ThemeAlias
    """Used for success-colored controls while hovered."""

    success_bg_pressed: ThemeAlias
    """Used for success-colored controls while pressed."""

    success_bg_disabled: ThemeAlias
    """Used for disabled success-colored controls."""

    information: ThemeAlias
    """Used as the information accent color."""

    information_fg: ThemeAlias
    """Used for information-colored texts and icons."""

    information_bg: ThemeAlias
    """Used for subtle information-colored backgrounds and selections."""

    information_bg_hover: ThemeAlias
    """Used for information-colored controls while hovered."""

    information_bg_pressed: ThemeAlias
    """Used for information-colored controls while pressed."""

    information_bg_disabled: ThemeAlias
    """Used for disabled information-colored controls."""
