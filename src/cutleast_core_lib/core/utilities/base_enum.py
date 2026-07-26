"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Any, Optional, Self, TypeVar, overload, override

T = TypeVar("T")


class BaseEnum(Enum):
    """
    Custom Enum class extended with some utility methods.
    """

    @overload
    @classmethod
    def get(cls, name: str, /) -> Optional[Self]: ...

    @overload
    @classmethod
    def get(cls, name: str, default: T, /) -> Self | T: ...

    @classmethod
    def get(cls, name: str, default: Optional[T] = None, /) -> Optional[Self | T]:
        """
        Gets an enum member by name.

        Args:
            name (str): Name of the enum member.
            default (T): Default value to return if no enum member has the given name.

        Returns:
            Self | T: Enum member or default value.
        """

        try:
            return cls[name]
        except KeyError:
            return default

    @overload
    @classmethod
    def get_by_value(cls, value: Any, /) -> Optional[Self]: ...

    @overload
    @classmethod
    def get_by_value(cls, value: Any, default: T, /) -> Self | T: ...

    @classmethod
    def get_by_value(
        cls, value: Any, default: Optional[T] = None, /
    ) -> Optional[Self | T]:
        """
        Gets an enum member by its value.

        Args:
            value (Any): Value of the enum member.
            default (T): Default value to return if no enum member has the given value.

        Returns:
            Self | T: Enum member or default value.
        """

        try:
            return cls(value)
        except KeyError:
            return default

    @override
    def __repr__(self) -> str:
        return self.name
