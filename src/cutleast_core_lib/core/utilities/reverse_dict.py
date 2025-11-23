"""
Copyright (c) Cutleast
"""

from typing import TypeVar

from .reference_dict import ReferenceDict

K = TypeVar("K")
V = TypeVar("V")


def reverse_dict(d: dict[K, V] | ReferenceDict[K, V], /) -> dict[V, K]:
    """
    Swaps the keys and values of a dictionary.

    Args:
        d (dict[K, V] | ReferenceDict[K, V]): The dictionary to reverse.

    Returns:
        dict[V, K]: The reversed dictionary.
    """

    return {v: k for k, v in d.items()}
