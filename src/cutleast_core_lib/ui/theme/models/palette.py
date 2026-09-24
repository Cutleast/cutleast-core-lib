"""
Copyright (c) Cutleast
"""

from typing import ClassVar, Self, cast

from material_color_utilities import Hct

from ..ui_mode import UiMode
from .base import ThemeModel
from .types import HexColorStr, ResolvedUiMode


class ColorPalette(ThemeModel):
    """
    A complete chromatic palette with 13 tones.
    """

    tone_0: HexColorStr = "#000000"
    tone_5: HexColorStr
    tone_10: HexColorStr
    tone_20: HexColorStr
    tone_30: HexColorStr
    tone_40: HexColorStr
    tone_50: HexColorStr
    tone_60: HexColorStr
    tone_70: HexColorStr
    tone_80: HexColorStr
    tone_90: HexColorStr
    tone_95: HexColorStr
    tone_100: HexColorStr = "#ffffff"

    DARK_CHROMA_FACTORS: ClassVar[dict[int, float]] = {
        0: 0.00,
        5: 0.10,
        10: 0.20,
        20: 0.35,
        30: 0.55,
        40: 0.75,
        50: 0.90,
        60: 1.00,
        70: 1.00,
        80: 1.00,
        90: 1.00,
        95: 1.00,
        100: 1.00,
    }

    LIGHT_CHROMA_FACTORS: ClassVar[dict[int, float]] = {
        0: 1.00,
        5: 1.00,
        10: 1.00,
        20: 1.00,
        30: 1.00,
        40: 1.00,
        50: 1.00,
        60: 0.90,
        70: 0.75,
        80: 0.55,
        90: 0.35,
        95: 0.20,
        100: 0.10,
    }

    @classmethod
    def from_seed_color(cls, seed_color: HexColorStr, ui_mode: ResolvedUiMode) -> Self:
        """
        Generates a color palette from a seed color.

        Args:
            seed_color (HexColorStr): The base color to generate the palette from.
            ui_mode (ResolvedUiMode):
                The UI mode for the palette. Determines the chroma factors used for tone
                generation.

        Returns:
            Self: A new color palette with generated tones.
        """

        return cls(
            tone_0=cls.get_color(seed_color, 0, ui_mode),
            tone_5=cls.get_color(seed_color, 5, ui_mode),
            tone_10=cls.get_color(seed_color, 10, ui_mode),
            tone_20=cls.get_color(seed_color, 20, ui_mode),
            tone_30=cls.get_color(seed_color, 30, ui_mode),
            tone_40=cls.get_color(seed_color, 40, ui_mode),
            tone_50=cls.get_color(seed_color, 50, ui_mode),
            tone_60=cls.get_color(seed_color, 60, ui_mode),
            tone_70=cls.get_color(seed_color, 70, ui_mode),
            tone_80=cls.get_color(seed_color, 80, ui_mode),
            tone_90=cls.get_color(seed_color, 90, ui_mode),
            tone_95=cls.get_color(seed_color, 95, ui_mode),
            tone_100=cls.get_color(seed_color, 100, ui_mode),
        )

    @classmethod
    def get_color(
        cls, seed_color: HexColorStr, tone: int, ui_mode: ResolvedUiMode
    ) -> HexColorStr:
        """
        Calculates a color tone from a base seed color.

        Args:
            seed_color (HexColorStr): The base color to calculate the color tone from.
            tone (int): The color tone to return.
            ui_mode (ResolvedUiMode):
                The UI mode for the color. Determines the chroma factors used for tone
                generation.

        Returns:
            HexColorStr: The calculated color.
        """

        color = Hct(seed_color)
        color.tone = tone
        if ui_mode == UiMode.Dark:
            color.chroma *= cls.DARK_CHROMA_FACTORS[tone]
        else:
            color.chroma *= cls.LIGHT_CHROMA_FACTORS[tone]

        return cast(HexColorStr, color.hex)
