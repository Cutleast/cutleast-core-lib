"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import Optional, Protocol, Self, TypeVar, cast, get_origin

_T = TypeVar("_T")


def checked_cast(type_hint: type[_T], value: object) -> _T:
    """
    Similar to `typing.cast` but checks the type of the specified value and raises a
    `TypeError` if the value does not conform the specified type.

    For generic types, this only checks the origin's type. For example, for `list[str]`,
    it is only checked, if the value is of type `list`. The subtype is neither
    inspectable nor checkable during runtime.

    Args:
        type_hint (type[_T]): Type to cast to.
        value (object): Value to cast.

    Raises:
        TypeError: If the value cannot be cast to the type.

    Returns:
        _T: The cast value.
    """

    if not isinstance(value, get_origin(type_hint) or type_hint):
        raise TypeError(
            f"Cannot cast value of type '{type(value).__name__}'"
            f" to '{type_hint.__name__}': {value!r}"
        )

    return cast(_T, value)


def not_none(value: Optional[_T]) -> _T:
    """
    Checks if the specified value is not `None` and raises a `ValueError` if it is.

    Args:
        value (Optional[_T]): Value to check.

    Raises:
        ValueError: If the value is `None`.

    Returns:
        _T: The value if it is not `None`.
    """

    if value is None:
        raise ValueError("Value cannot be None")

    return value


class Comparable(Protocol):
    """Protocol for annotating comparable types."""

    @abstractmethod
    def __lt__(self, other: Self, /) -> bool:
        pass
