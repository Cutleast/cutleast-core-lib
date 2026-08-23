"""
Copyright (c) Cutleast
"""

import re
from typing import Annotated, Optional

from pydantic import Field
from PySide6.QtGui import QFont

from .base import ThemeModel
from .types import QSS_SIZE_PATTERN, QssSizeStr, ThemeAlias


class FontStyle(ThemeModel):
    """
    A reusable font definition.
    """

    family: str
    """The font family name."""

    size: QssSizeStr
    """The font size in QSS format (e.g., '12px', '1.5em')."""

    weight: Annotated[int, Field(ge=100, le=900, multiple_of=100)]
    """The font weight (e.g., 400 for normal, 700 for bold) between 100 and 900."""

    color: ThemeAlias
    """The font color, either as a hexadecimal string or a token reference."""

    def as_qfont(self) -> QFont:
        """
        Creates a QFont object based on the font definition.
        Note that the color is not applied to the QFont object.

        Returns:
            QFont: The corresponding QFont object.
        """

        font = QFont(self.family)
        font.setWeight(QFont.Weight(self.weight))
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)

        match: Optional[re.Match[str]] = QSS_SIZE_PATTERN.fullmatch(self.size)
        if match is None:
            raise ValueError(f"Invalid QSS size value: {self.size!r}")

        value = float(match.group(1))
        unit: str = match.group(2)

        match unit:
            case "px":
                font.setPixelSize(round(value))

            case "pt":
                font.setPointSizeF(value)

            case "em":
                raise ValueError(
                    "Font sizes using the 'em' unit cannot be applied directly to QFont."
                )

            case _:
                raise ValueError(f"Unsupported QSS size unit: {unit!r}")

        return font
