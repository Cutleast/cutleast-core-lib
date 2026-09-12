"""
Copyright (c) Cutleast
"""

from collections.abc import Callable
from threading import Lock
from typing import Generic, TypeVar, cast, final

T = TypeVar("T")

_UNSET = object()


@final
class Lazy(Generic[T]):
    """
    Lazily creates and caches a value.

    The supplier is called exactly once when the value is requested for the
    first time. Subsequent calls return the cached value.

    The cached value can be replaced explicitly through the value property.

    If the supplier raises an exception, no value is cached and the supplier
    is called again on the next access.
    """

    _supplier: Callable[[], T]
    _value: T | object
    _lock: Lock

    def __init__(self, supplier: Callable[[], T]) -> None:
        """
        Args:
            supplier (Callable[[], T]):
                Callable used to create the value on first access.
        """

        self._supplier = supplier
        self._value = _UNSET
        self._lock = Lock()

    @classmethod
    def from_value(cls, value: T) -> Lazy[T]:
        """
        Creates an already initialized lazy value.

        Args:
            value (T): Initial static value.

        Returns:
            Lazy[T]: Initialized lazy value.
        """

        lazy = cls(lambda: value)
        lazy.value = value
        return lazy

    @property
    def has_value(self) -> bool:
        """If the value has been created and cached or assigned."""

        return self._value is not _UNSET

    @property
    def value(self) -> T:
        """The cached value or creates it on first access."""

        if self._value is _UNSET:
            with self._lock:
                if self._value is _UNSET:
                    self._value = self._supplier()

        return cast(T, self._value)

    @value.setter
    def value(self, value: T) -> None:
        """
        Replaces the cached value.

        Assigning a value marks this instance as initialized without invoking
        the supplier.

        Args:
            value (T): New cached value.
        """

        with self._lock:
            self._value = value

    def reset(self) -> None:
        """
        Resets the value by clearing it, resulting in the supplier to be invoked on the
        next access.
        """

        with self._lock:
            self._value = _UNSET

    def __call__(self) -> T:
        """
        Returns the cached value or creates it on first access.

        Returns:
            T: The cached or lazily created value.
        """

        return self.value
