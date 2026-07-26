"""
Copyright (c) Cutleast
"""

import re
from collections.abc import Callable
from typing import Optional


def substitute(text: str, placeholders: dict[str, str], pattern: str) -> str:
    """
    Substitutes all placeholder occurences in a string according to a regex pattern.

    If the pattern contains a "key" group, the value of that group will be used to look
    up the replacement value in the placeholders dictionary. If no such group exists,
    the first capturing group is used.

    Args:
        text (str): Text to substitute placeholders in.
        placeholders (dict[str, str]): Placeholder values to insert.
        pattern (str): Regex pattern describing a placeholder.

    Returns:
        str: The text with substituted placeholders.
    """

    return substitute_advanced(text, placeholders.get, pattern)


def substitute_advanced(
    text: str, replacer: Callable[[str], Optional[str]], pattern: str
) -> str:
    """
    Substitutes all placeholder occurences in a string according to a regex pattern.

    If the pattern contains a "key" group, the value of that group will be used to look
    up the replacement value in the placeholders dictionary. If no such group exists,
    the first capturing group is used.
    If a placeholder cannot be resolved, it will be left unchanged.

    Args:
        text (str): Text to substitute placeholders in.
        replacer (Callable[[str], Optional[str]]):
            Function that takes a placeholder key and returns its replacement or None.
        pattern (str): Regex pattern describing a placeholder.

    Returns:
        str: The text with substituted placeholders.
    """

    placeholder_pattern: re.Pattern[str] = re.compile(pattern)

    def repl(match: re.Match[str]) -> str:
        key: str = match.group("key") if "key" in match.groupdict() else match.group(1)
        replacement: Optional[str] = replacer(key)
        return replacement if replacement is not None else match.group(0)

    return placeholder_pattern.sub(repl, text)
