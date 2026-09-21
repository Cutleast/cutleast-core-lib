"""
Copyright (c) Cutleast
"""

from collections.abc import Callable, Hashable, Iterable
from typing import Optional, TypeVar

T = TypeVar("T")


def unique(
    iterable: Iterable[T], key: Optional[Callable[[T], Hashable]] = None
) -> list[T]:
    """
    Removes all duplicates from an iterable.

    Args:
        iterable (Iterable[T]): Iterable with duplicates.
        key (Optional[Callable[[T], Hashable]], optional):
            Key function to identify unique elements. Defaults to None.

    Returns:
        list[T]: List without duplicates.
    """

    if key is None:
        return list({item: None for item in iterable}.keys())

    else:
        return list({key(item): item for item in iterable}.values())
