"""
Copyright (c) Cutleast
"""

from os import getenv
from pathlib import Path
from typing import Optional, TypeVar, cast

from .substitute import substitute_advanced

_StringOrPath = TypeVar("_StringOrPath", str, Path)


def resolve(
    str_or_path: _StringOrPath, sep: tuple[str, str] = ("%", "%"), **vars: str
) -> _StringOrPath:
    """
    Resolves all (environment) variables in a string or path.

    Args:
        str_or_path (_StringOrPath): String or path with (environment) variables.
        sep (tuple[str, str], optional): Placeholder indicators, for eg. `("{", "}")`.
        vars (str): Additional variables to resolve.

    Returns:
        _StringOrPath: Resolved string or path
    """

    norm_vars: dict[str, str] = {key.lower(): value for key, value in vars.items()}

    def replacer(key: str) -> Optional[str]:
        return norm_vars.get(key.lower(), getenv(key))

    if isinstance(str_or_path, Path):
        parts: list[str] = []
        for part in str_or_path.parts:
            parts.append(
                substitute_advanced(part, replacer, f"^{sep[0]}([a-zA-Z0-9_]*){sep[1]}$")
            )

        return cast(_StringOrPath, Path(*parts))

    else:
        return substitute_advanced(
            str_or_path, replacer, f"{sep[0]}([a-zA-Z0-9_]*){sep[1]}"
        )
