"""
Copyright (c) Cutleast
"""

from typing import Annotated

from pydantic import BeforeValidator

from ..ui_mode import UiMode
from .base import ThemeModel
from .colors import ColorAliases
from .meta import MetaAttributes
from .metrics import ThemeMetrics
from .palette import ColorPalette
from .texts import TextStyles
from .types import HexColorStr, ResolvedUiMode


class ThemeDefinition(ThemeModel):
    """
    Model for the raw definition of a theme.
    """

    ui_mode: Annotated[ResolvedUiMode, BeforeValidator(lambda v: UiMode(v))]
    """UI mode the theme belongs to."""

    colors: ColorAliases
    """Semantic color aliases."""

    neutral_palette: ColorPalette
    """Neutral color palette."""

    error_color: HexColorStr
    """Base for the error color palette."""

    caution_color: HexColorStr
    """Base for the caution color palette."""

    warning_color: HexColorStr
    """Base for the warning color palette."""

    success_color: HexColorStr
    """Base for the success color palette."""

    information_color: HexColorStr
    """Base for the information color palette."""

    texts: TextStyles
    """Semantic text styles."""

    metrics: ThemeMetrics
    """Theme metrics for spacings and borders."""

    resources: Annotated[
        MetaAttributes, BeforeValidator(lambda v: MetaAttributes(v))
    ] = MetaAttributes()
    """Resource tokens for the theme."""

    meta: Annotated[MetaAttributes, BeforeValidator(lambda v: MetaAttributes(v))] = (
        MetaAttributes()
    )
    """Additional attributes for the theme."""
