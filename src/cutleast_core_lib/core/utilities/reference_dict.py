"""
Copyright (c) Cutleast
"""

from collections.abc import Iterator, MutableMapping
from typing import Generic, Optional, TypeVar, overload, override

K = TypeVar("K")
V = TypeVar("V")
_MISSING: object = object()


class ReferenceDict(MutableMapping[K, V], Generic[K, V]):
    """
    Dict-like container that uses object identity (`id()`) instead of hash equality as
    the key discriminator.

    This makes it suitable for mutable objects that cannot be (or should not be) used as
    dict keys, because it does not require the key type to be hashable. Two distinct
    objects that compare equal are treated as different keys.

    This class provides all features of the `Mapping` protocol.
    """

    __values: dict[int, tuple[K, V]]

    def __init__(
        self,
        initial: Optional[dict[K, V]] = None,
    ) -> None:
        """
        Initialises the container.

        Args:
            initial (Optional[dict[K, V]]):
                Optional mapping whose key-value pairs are copied into this container.
                Each key is registered by its current `id()`.  Defaults to an empty
                mapping when `None`.
        """

        if initial is None:
            initial = {}

        self.__values = {id(k): (k, v) for k, v in initial.items()}

    @override
    def __getitem__(self, key: K) -> V:
        try:
            return self.__values[id(key)][1]
        except KeyError:
            raise KeyError(key) from None

    @override
    def __setitem__(self, key: K, value: V) -> None:
        self.__values[id(key)] = (key, value)

    @override
    def __delitem__(self, key: K) -> None:
        try:
            del self.__values[id(key)]
        except KeyError:
            raise KeyError(key) from None

    @override
    def __iter__(self) -> Iterator[K]:
        for key, _ in self.__values.values():
            yield key

    @override
    def __len__(self) -> int:
        return len(self.__values)

    @override
    def __contains__(self, key: object) -> bool:
        return id(key) in self.__values

    @overload
    def pop(self, key: K) -> V: ...

    @overload
    def pop(self, key: K, default: V) -> V: ...

    @overload
    def pop(self, key: K, default: object) -> object: ...

    @override
    def pop(
        self,
        key: K,
        default: object = _MISSING,
    ) -> object:
        try:
            return self.__values.pop(id(key))[1]
        except KeyError:
            if default is _MISSING:
                raise KeyError(key) from None
            return default

    @override
    def clear(self) -> None:
        self.__values.clear()

    @override
    def __repr__(self) -> str:
        pairs = ", ".join(f"'{k}': '{v}'" for k, v in self.__values.values())
        return f"{type(self).__name__}({{{pairs}}})"
