"""
Copyright (c) Cutleast
"""

from .base import ThemeModel
from .font import FontStyle


class TextStyles(ThemeModel):
    """
    Semantic text styles used by the application.
    """

    title: FontStyle
    """Used for primary page and dialog titles."""

    subtitle: FontStyle
    """Used for section headings and secondary titles."""

    text: FontStyle
    """Used for regular application text."""

    emphasized: FontStyle
    """Used for emphasized text without changing its semantic hierarchy."""

    secondary: FontStyle
    """Used for secondary information, hints, and metadata."""

    monospace: FontStyle
    """Used for code, paths, identifiers, logs, and other fixed-width content."""
