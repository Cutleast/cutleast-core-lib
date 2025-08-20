"""
Copyright (c) Cutleast
"""

import logging
import sys
from types import TracebackType
from typing import Callable
from winsound import MessageBeep as alert

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from cutleast_core_lib.ui.widgets.error_dialog import ErrorDialog

from .exceptions import LocalizedException, format_exception


class ExceptionHandler(QObject):
    """
    Redirects uncatched exceptions to an ErrorDialog instead of crashing the entire app.
    """

    log: logging.Logger = logging.getLogger("ExceptionHandler")
    __sys_excepthook: (
        Callable[[type[BaseException], BaseException, TracebackType | None], None]
        | None
    ) = None

    __parent: QApplication

    def __init__(self, parent: QApplication) -> None:
        super().__init__(parent)

        self.__parent = parent

        self.bind_hook()

    def bind_hook(self) -> None:
        """
        Binds ExceptionHandler to `sys.excepthook`.
        """

        if self.__sys_excepthook is None:
            self.__sys_excepthook = sys.excepthook
            sys.excepthook = self.__exception_hook

    def unbind_hook(self) -> None:
        """
        Unbinds ExceptionHandler and restores original `sys.excepthook`.
        """

        if self.__sys_excepthook is not None:
            sys.excepthook = self.__sys_excepthook
            self.__sys_excepthook = None

    def __exception_hook(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        """
        Redirects uncatched exceptions and shows them in an ErrorDialog.
        """

        # Pass through if exception is KeyboardInterrupt (Ctrl + C)
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        traceback = format_exception(exc_value, only_message_when_localized=False)
        self.log.critical("An uncaught exception occured:\n" + traceback)

        error_message: str
        if isinstance(exc_value, LocalizedException):
            error_message = str(exc_value)
        else:
            error_message = self.tr("An unexpected error occured: ") + str(exc_value)
        detailed_msg = traceback

        error_dialog = ErrorDialog(
            parent=self.__parent.activeModalWidget(),
            title=self.tr("Error"),
            text=error_message,
            details=detailed_msg,
            yesno=not isinstance(exc_value, LocalizedException),
        )

        # Play system alarm sound
        alert()

        choice = error_dialog.exec()

        if choice == ErrorDialog.DialogCode.Accepted:
            self.__parent.exit()

    @staticmethod
    def raises_exception(
        callable: Callable, expected_exception: type[BaseException] | None = None
    ) -> bool:
        """
        Checks if the callable raises the expected exception.

        Args:
            callable (Callable): Function or method to check.
            expected_exception (type[BaseException] | None, optional):
                Expected exception. Defaults to None.

        Raises:
            Exception: If the callable does not raise the expected exception.

        Returns:
            bool: `True` if the callable raises the expected exception, `False` otherwise.
        """

        try:
            callable()
        except Exception as ex:
            if expected_exception is not None and not isinstance(
                ex, expected_exception
            ):
                raise ex

            return True

        return False
