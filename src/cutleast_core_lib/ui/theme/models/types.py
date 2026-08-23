"""
Copyright (c) Cutleast
"""

import re
from typing import Annotated, Literal, TypeAlias

from pydantic import Field

from ..ui_mode import UiMode

HEX_COLOR_PATTERN: re.Pattern[str] = re.compile(
    r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", re.IGNORECASE
)
"""Regular expression pattern for validating hexadecimal color strings."""

TOKEN_GROUP_KEY: str = "key"
"""Name of the capturing group for the key in tokenized strings."""

TOKEN_PATTERN: re.Pattern[str] = re.compile(
    r"\$\{(?P<" + TOKEN_GROUP_KEY + r">[a-z\.\_0-9]+?)\}"
)
"""
Regular expression pattern for matching tokenized strings in the format `${key.subkey}`.
"""

QSS_SIZE_PATTERN: re.Pattern[str] = re.compile(r"^(-?\d*\.?\d+)(px|em|pt)$")
"""Regular expression pattern for validating size values in QSS format."""

HexColorStr: TypeAlias = Annotated[str, Field(pattern=HEX_COLOR_PATTERN)]
"""Type alias for all strings representing hexadecimal color values."""

TokenRef: TypeAlias = Annotated[str, Field(pattern=TOKEN_PATTERN)]
"""Type alias for all strings referencing tokens in the format `${key}`."""

QssSizeStr: TypeAlias = Annotated[str, Field(pattern=QSS_SIZE_PATTERN)]
"""Type alias for all strings representing size values in QSS format."""

ThemeAlias: TypeAlias = HexColorStr | TokenRef
"""Type alias for all strings that can either be a hexadecimal color or a token reference."""

ResolvedUiMode: TypeAlias = Literal[UiMode.Dark, UiMode.Light]
"""Type alias for resolved UI modes: either dark or light."""
