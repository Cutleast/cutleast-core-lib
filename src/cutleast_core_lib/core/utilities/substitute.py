"""
Copyright (c) Cutleast
"""

import re


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

    placeholder_pattern: re.Pattern[str] = re.compile(pattern)

    return placeholder_pattern.sub(
        lambda match: placeholders.get(match.group("key"), match.group(1)), text
    )
