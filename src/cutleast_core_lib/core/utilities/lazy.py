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

    @property
    def is_initialized(self) -> bool:
        """If the value has been created and cached."""

        return self._value is not _UNSET

    @property
    def value(self) -> T:
        """The cached value or creates it on first access."""

        if self._value is _UNSET:
            with self._lock:
                if self._value is _UNSET:
                    self._value = self._supplier()

        return cast(T, self._value)

    def __call__(self) -> T:
        """
        Returns the cached value or creates it on first access.

        Returns:
            T: The lazily created value.
        """

        return self.value
