"""
Copyright (c) Cutleast
"""

from typing import Callable, Generic, TypeVar, override

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget

from .exceptions import ProcessIncompleteError

T = TypeVar("T")


def process_result(result: T | Exception) -> T:
    """
    Processes a thread result by raising it if it is an exception.

    Args:
        result (T | Exception): The result to process.

    Raises:
        Exception: If the result is an exception.

    Returns:
        T: The processed result.
    """

    if isinstance(result, Exception):
        raise result

    return result


class Thread(QThread, Generic[T]):
    """
    Adapted QThread with a generic return type.
    """

    __target: Callable[[], T]
    __return_result: T | Exception

    def __init__(
        self,
        target: Callable[[], T],
        name: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.__target = target

        if name is not None:
            self.setObjectName(name)

    @override
    def run(self) -> None:
        """
        Runs the target function, storing its return value or an exception.
        """

        try:
            self.__return_result = self.__target()
        except Exception as ex:
            self.__return_result = ex

    def get_result(self) -> T | Exception:
        """
        Returns the return value of the target function or an exception.

        Raises:
            ProcessIncompleteError:
                If the result of the thread was requested before the thread was finished
                or when it was terminated.

        Returns:
            T | Exception: Return value of the target function or an exception
        """

        try:
            return self.__return_result
        except AttributeError:
            raise ProcessIncompleteError from AttributeError
