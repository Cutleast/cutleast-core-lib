"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from cutleast_core_lib.core.utilities.singleton import SingletonQObject


class WindowManager(SingletonQObject):
    """
    Singleton class to manage the life-cycle of non-modal windows in an application.
    """

    __windows: dict[int, QWidget]

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__windows = {}

    def show(self, window: QWidget, delete_on_close: bool = True) -> None:
        """
        Registers and shows a non-modal window.

        Args:
            window (QWidget): Window to keep alive.
            delete_on_close (bool, optional):
                If the window should be deleted when closed. Defaults to True.
        """

        window_id: int = id(window)
        self.__windows[window_id] = window

        if delete_on_close:
            window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
            window.destroyed.connect(lambda *_: self.__windows.pop(window_id, None))

        window.show()

    def close_all(self) -> None:
        """
        Closes all managed windows.
        """

        for window in list(self.__windows.values()):
            window.close()
