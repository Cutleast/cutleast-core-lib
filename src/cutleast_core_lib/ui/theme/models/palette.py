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

        seed = Hct(seed_color)

        def get_color(tone: int) -> HexColorStr:
            color = Hct(seed_color)
            color.tone = tone

            if ui_mode == UiMode.Dark:
                color.chroma = seed.chroma * cls.DARK_CHROMA_FACTORS[tone]
            else:
                color.chroma = seed.chroma * cls.LIGHT_CHROMA_FACTORS[tone]

            return cast(HexColorStr, color.hex)

        return cls(
            tone_0=get_color(0),
            tone_5=get_color(5),
            tone_10=get_color(10),
            tone_20=get_color(20),
            tone_30=get_color(30),
            tone_40=get_color(40),
            tone_50=get_color(50),
            tone_60=get_color(60),
            tone_70=get_color(70),
            tone_80=get_color(80),
            tone_90=get_color(90),
            tone_95=get_color(95),
            tone_100=get_color(100),
        )
