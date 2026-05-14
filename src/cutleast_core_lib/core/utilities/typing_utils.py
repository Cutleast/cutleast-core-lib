"""
Copyright (c) Cutleast
"""

from typing import Optional, TypeVar

_T = TypeVar("_T")


def checked_cast(type_hint: type[_T], value: object) -> _T:
    """
    Similar to `typing.cast` but checks the type of the specified value and raises a
    `TypeError` if the value does not conform the specified type.

    Args:
        type_hint (type[_T]): Type to cast to.
        value (object): Value to cast.

    Raises:
        TypeError: If the value cannot be cast to the type.

    Returns:
        _T: The cast value.
    """

    if not isinstance(value, type_hint):
        raise TypeError(
            f"Cannot cast value of type '{type(value).__name__}'"
            f" to '{type_hint.__name__}': {value!r}"
        )

    return value


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
