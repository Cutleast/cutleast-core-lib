"""
Copyright (c) Cutleast
"""

import traceback
from abc import abstractmethod
from typing import Any, Callable, ParamSpec, TypeVar, override

from PySide6.QtWidgets import QApplication

# Nuitka doesn't support the new syntax, yet, see https://github.com/Nuitka/Nuitka/issues/3423
T = TypeVar("T")
P = ParamSpec("P")


def format_exception(
    exception: BaseException, only_message_when_localized: bool = True
) -> str:
    """
    Formats an exception to a string.

    Args:
        exception (BaseException): The exception to format.
        only_message_when_localized (bool):
            Whether to only return the message when localized.

    Returns:
        str: Formatted exception
    """

    if isinstance(exception, LocalizedException) and only_message_when_localized:
        return str(exception)

    return "".join(traceback.format_exception(exception))


class LocalizedException(Exception):
    """
    Base exception class for localized exceptions.
    """

    def __init__(self, *values: Any) -> None:
        if self.getLocalizedMessage():
            super().__init__(self.getLocalizedMessage().format(*values))
        else:
            super().__init__(*values)

    @abstractmethod
    def getLocalizedMessage(self) -> str:
        """
        Returns localised message

        Returns:
            str: Localised message
        """

    @classmethod
    def wrap(cls, func_or_meth: Callable[P, T]) -> Callable[P, T]:
        """
        Wraps function or method in a try-except-block
        that raises an exception of this type.

        Args:
            func_or_meth (F): Function or method

        Returns:
            F: Wrapped function or method
        """

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func_or_meth(*args, **kwargs)
            except Exception as e:
                raise cls() from e

        return wrapper


class RequestError(LocalizedException):
    """
    Exception when a web request failed.
    """

    def __init__(self, request_url: str, *values: Any) -> None:
        super().__init__(request_url, *values)

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Request to '{0}' failed!")


class Non200HttpError(RequestError):
    """
    Exception when a request returned a non-200 HTTP status code.
    """

    def __init__(self, request_url: str, status_code: int) -> None:
        super().__init__(request_url, status_code)

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "Request to '{0}' failed with status code {1}!"
        )
