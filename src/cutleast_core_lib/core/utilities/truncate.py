"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Optional


class TruncateMode(Enum):
    """Truncation mode."""

    Start = "start"
    """
    Truncates the string at the beginning.
    
    Example:     
        >>> truncate_string("Hello, world!", 10, TruncateMode.Start)
        '... world!'
    """

    Middle = "middle"
    """
    Truncates the string in the middle.
    
    Example:     
        >>> truncate_string("Hello, world!", 10, TruncateMode.Middle)
        'Hel...rld!'
    """

    End = "end"
    """
    Truncates the string at the end.
    
    Example:     
        >>> truncate_string("Hello, world!", 10, TruncateMode.End)
        'Hello, ...'
    """


def truncate_string(
    s: str,
    max_length: int,
    mode: TruncateMode = TruncateMode.End,
    placeholder: str = "...",
) -> str:
    """
    Truncates a string to a specified maximum length using a placeholder.

    Args:
        s (str): The original string.
        max_length (int):
            The maximum allowed length of the result (including placeholder).
        mode (TruncateMode, optional):
            Where to truncate the string: start, middle, or end. Defaults to
            TruncateMode.End.
        placeholder (str, optional): The truncation indicator. Defaults to "...".

    Returns:
        str: The truncated string, if necessary.

    Raises:
        ValueError: If max_length is less than the length of the placeholder.
    """

    if len(s) <= max_length:
        return s

    if max_length < len(placeholder):
        raise ValueError(
            "max_length must be at least as long as the placeholder length."
        )

    remaining: int = max_length - len(placeholder)

    match mode:
        case TruncateMode.End:
            return s[:remaining] + placeholder
        case TruncateMode.Start:
            return placeholder + s[-remaining:]
        case TruncateMode.Middle:
            half: int = remaining // 2
            return s[:half] + placeholder + s[-(remaining - half) :]


def raw_string(text: str, max_length: Optional[int] = 100) -> str:
    r"""
    Returns raw representation (for eg. "\\n" instead of a line break) of a text
    trimmed to a specified number of characters.
    Appends "..." suffix if the text was longer than the specified length.

    Args:
        text (str): String to trim.
        max_length (Optional[int], optional):
            Maximum length of trimmed string. If None, the string is not trimmed at all.
            Defaults to 100.

    Returns:
        str: Trimmed string
    """

    if max_length is None:
        return f"{text!r}"[1:-1]

    return truncate_string(f"{text!r}"[1:-1], max_length)
