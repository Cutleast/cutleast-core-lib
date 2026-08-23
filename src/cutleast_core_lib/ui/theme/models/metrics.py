"""
Copyright (c) Cutleast
"""

from .base import ThemeModel
from .types import QssSizeStr


class ThemeMetrics(ThemeModel):
    """
    Fixed metrics used throughout the application theme.
    """

    spacing_xs: QssSizeStr
    """Extra small spacing value for very compact gaps and padding."""

    spacing_s: QssSizeStr
    """Small spacing value for compact gaps and padding."""

    spacing_ms: QssSizeStr
    """Medium-small spacing value for gaps and padding."""

    spacing: QssSizeStr
    """Default spacing value for gaps and padding."""

    spacing_l: QssSizeStr
    """Large spacing value for sections and spacious padding."""

    radius_xs: QssSizeStr
    """Extra small border radius used by very compact widgets."""

    radius_s: QssSizeStr
    """Small border radius used by compact widgets."""

    radius_ms: QssSizeStr
    """Medium-small border radius used by widgets and containers."""

    radius: QssSizeStr
    """Default border radius used by widgets and containers."""

    radius_l: QssSizeStr
    """Large border radius used by larger surfaces and containers."""

    border_width: QssSizeStr
    """Default border width."""

    border_width_focus: QssSizeStr
    """Border width used to emphasize focused widgets."""

    icon_s: int
    """Small icon size in pixels used in compact buttons and controls."""

    icon_ms: int
    """Medium-small icon size in pixels used in standard buttons and controls."""

    icon: int
    """Default icon size in pixels used in standard buttons and controls."""

    icon_l: int
    """Large icon size in pixels used in prominent buttons and controls."""

    icon_xl: int
    """Extra large icon size in pixels used in prominent buttons and controls."""

    shadow_margin: int
    """Space in pixels reserved around elevated transient surfaces for their shadow."""

    shadow_size: int
    """Blur radius in pixels used for shadows cast by elevated transient surfaces."""
