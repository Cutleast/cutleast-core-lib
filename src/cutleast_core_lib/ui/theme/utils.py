"""
Copyright (c) Cutleast
"""

import re
from typing import Any, Optional, TypeVar

T = TypeVar("T")


class CyclicReferenceError(ValueError):
    """
    Raised when resolving an attribute path encounters a cyclic reference.
    """


def resolve_attr_reference(
    root: object, reference: str, pattern: re.Pattern[str], group_name: str
) -> Any:
    """
    Resolves an attribute reference and follows chained references.

    The supplied regular expression determines whether a string represents a
    reference. The named capturing group specified by `group_name` must contain
    the dotted attribute path.

    Args:
        root (object): Root object from which all paths are resolved.
        reference (str): Initial reference to resolve.
        pattern (re.Pattern[str]): Pattern used to recognize references.
        group_name (str): Name of the capturing group containing the path.

    Returns:
        Any: Final resolved value.

    Raises:
        ValueError: If the initial reference does not match the pattern.
        AttributeError: If a referenced attribute does not exist.
        IndexError: If the configured capturing group does not exist.
        CyclicReferenceError: If a cyclic reference is detected.
    """

    match: Optional[re.Match[str]] = pattern.fullmatch(reference)
    if match is None:
        raise ValueError(f"Invalid reference: {reference!r}")

    current_path: str = match.group(group_name)
    visited: set[str] = set()
    chain: list[str] = []

    while True:
        if current_path in visited:
            cycle_start: int = chain.index(current_path)
            cycle: list[str] = chain[cycle_start:] + [current_path]

            raise CyclicReferenceError(
                "Cyclic attribute reference detected: " + " -> ".join(cycle)
            )

        visited.add(current_path)
        chain.append(current_path)

        value = _resolve_attr_path(root, current_path)

        if not isinstance(value, str):
            return value

        match = pattern.fullmatch(value)
        if match is None:
            return value

        current_path = match.group(group_name)


def _resolve_attr_path(root: object, path: str) -> Any:
    """
    Resolves a dotted attribute path against an object.

    Args:
        root (object): Root object from which the path is resolved.
        path (str): Dotted attribute path to resolve.

    Returns:
        Any: Referenced attribute value.

    Raises:
        AttributeError: If an attribute in the path does not exist.
    """

    value: Any = root

    for key in path.split("."):
        value = getattr(value, key)

    return value
