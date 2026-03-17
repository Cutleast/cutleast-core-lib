"""
Copyright (c) Cutleast
"""

from typing import Mapping, TypeVar

K = TypeVar("K")
V = TypeVar("V")


def reverse_dict(d: Mapping[K, V], /) -> dict[V, K]:
    """
    Swaps the keys and values of a dictionary.

    Args:
        d (Mapping[K, V]): The dictionary to reverse.

    Returns:
        dict[V, K]: The reversed dictionary.
    """

    return {v: k for k, v in d.items()}
