"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial, update_wrapper, wraps
from types import MethodType
from typing import (
    Any,
    Concatenate,
    Generic,
    Optional,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)
from weakref import ReferenceType, ref

from PySide6.QtCore import QObject, QTimer

P = ParamSpec("P")
Q = ParamSpec("Q")
R = TypeVar("R")
T = TypeVar("T")


class _DebounceState(QObject):
    """
    Manages one independent trailing-edge debounce timer.
    """

    __pending_call: Optional[Callable[[], object]]
    __timer: QTimer

    def __init__(self, interval: int, parent: Optional[QObject] = None) -> None:
        """
        Args:
            interval (int): Debounce interval in milliseconds.
            parent (Optional[QObject], optional): QObject parent. Defaults to None.
        """

        super().__init__(parent)

        self.__pending_call = None

        self.__timer = QTimer(self)
        self.__timer.setInterval(interval)
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.__invoke)

    def schedule(self, callback: Callable[[], object]) -> None:
        """
        Schedules the specified callback after the debounce interval.

        Args:
            callback (Callable[[], object]): Callback to schedule.
        """

        self.__pending_call = callback
        self.__timer.start()

    def __invoke(self) -> None:
        """
        Invokes the most recently scheduled callback.
        """

        pending_call: Optional[Callable[[], object]] = self.__pending_call
        self.__pending_call = None

        if pending_call is not None:
            pending_call()


_MethodState = tuple[ReferenceType[object], _DebounceState]


class _DebouncedCallable(Generic[P, R]):
    """
    Wraps a callable with trailing-edge debounce behavior.
    """

    __callback: Callable[P, R]
    __function_state: Optional[_DebounceState]
    __interval: int
    __method_states: dict[int, _MethodState]

    def __init__(self, callback: Callable[P, R], interval: int) -> None:
        """
        Args:
            callback (Callable[P, R]): Callable to debounce.
            interval (int): Debounce interval in milliseconds.
        """

        self.__callback = callback
        self.__interval = interval
        self.__function_state = None
        self.__method_states = {}

        update_wrapper(self, callback)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """
        Schedules the wrapped standalone callable.

        Args:
            *args (P.args): Positional arguments for the wrapped callable.
            **kwargs (P.kwargs): Keyword arguments for the wrapped callable.
        """

        state: _DebounceState = self.__get_function_state()
        state.schedule(partial(self.__callback, *args, **kwargs))

    @overload
    def __get__(
        self: _DebouncedCallable[Concatenate[T, Q], R],
        instance: None,
        _owner: Optional[type[T]] = None,
    ) -> Callable[Concatenate[T, Q], None]: ...

    @overload
    def __get__(
        self: _DebouncedCallable[Concatenate[T, Q], R],
        instance: T,
        _owner: Optional[type[T]] = None,
    ) -> Callable[Q, None]: ...

    def __get__(
        self: _DebouncedCallable[Concatenate[T, Q], R],
        instance: Optional[T],
        _owner: Optional[type[T]] = None,
    ) -> Callable[Concatenate[T, Q], None] | Callable[Q, None]:
        """
        Returns a debounced callable for class or instance access.

        Args:
            instance (Optional[T]): Instance to bind, if accessed through an instance.
            _owner (Optional[type[T]], optional): Owning class. Defaults to None.

        Returns:
            Callable[..., None]: Debounced callable with the appropriate binding.
        """

        @wraps(self.__callback)  # pyrefly: ignore [no-access]
        def unbound(target: T, *args: Q.args, **kwargs: Q.kwargs) -> None:
            """
            Schedules the wrapped method for the specified instance.

            Args:
                target (T): Instance on which to invoke the wrapped method.
                *args (Q.args): Positional arguments for the wrapped method.
                **kwargs (Q.kwargs): Keyword arguments for the wrapped method.
            """

            state: _DebounceState = self.__get_method_state(target)  # pyrefly: ignore [no-access]
            state.schedule(partial(self.__callback, target, *args, **kwargs))  # pyrefly: ignore [no-access]

        if instance is None:
            return unbound

        # MethodType does not preserve the bound ParamSpec in its type information.
        return cast(Callable[Q, None], MethodType(unbound, instance))

    def __get_function_state(self) -> _DebounceState:
        """
        Returns the debounce state used for standalone calls.

        Returns:
            _DebounceState: State used for standalone calls.
        """

        state: Optional[_DebounceState] = self.__function_state

        if state is None:
            state = _DebounceState(self.__interval)
            self.__function_state = state

        return state

    def __get_method_state(self, instance: object) -> _DebounceState:
        """
        Returns the debounce state associated with the specified instance.

        Args:
            instance (object): Instance whose debounce state is requested.

        Returns:
            _DebounceState: State associated with the instance.

        Raises:
            TypeError: The instance does not support weak references.
        """

        # State belongs to object identity regardless of custom equality semantics.
        key: int = id(instance)
        entry: Optional[_MethodState] = self.__method_states.get(key)

        if entry is not None and entry[0]() is instance:
            return entry[1]

        try:
            instance_reference: ReferenceType[object] = ref(
                instance,
                partial(self.__remove_method_state, key),
            )
        except TypeError as ex:
            raise TypeError(
                "Debounced methods require weak-referenceable instances."
            ) from ex

        parent: Optional[QObject] = instance if isinstance(instance, QObject) else None
        state = _DebounceState(self.__interval, parent)
        self.__method_states[key] = (instance_reference, state)

        return state

    def __remove_method_state(
        self, key: int, instance_reference: ReferenceType[object]
    ) -> None:
        """
        Removes the state belonging to a garbage-collected instance.

        Args:
            key (int): Identity key of the collected instance.
            instance_reference (ReferenceType[object]): Weak reference to the instance.
        """

        entry: Optional[_MethodState] = self.__method_states.get(key)

        if entry is not None and entry[0] is instance_reference:
            del self.__method_states[key]


def debounce(interval: int) -> Callable[[Callable[P, Any]], Callable[P, None]]:
    """
    Creates a trailing-edge debounce decorator.

    Args:
        interval (int): Debounce interval in milliseconds.

    Returns:
        Callable[[Callable[P, Any]], Callable[P, None]]: Debounce decorator.

    Raises:
        ValueError: The debounce interval is negative.
    """

    if interval < 0:
        raise ValueError("Debounce interval must not be negative.")

    def decorator(callback: Callable[P, Any]) -> Callable[P, None]:
        """
        Wraps the specified callable with debounce behavior.

        Args:
            callback (Callable[P, R]): Callable to debounce.

        Returns:
            Callable[P, None]: Debounced callable.
        """

        debounced_callable = _DebouncedCallable(callback, interval)
        return cast(Callable[P, None], debounced_callable)

    return decorator
