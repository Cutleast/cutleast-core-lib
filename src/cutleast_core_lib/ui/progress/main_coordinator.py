"""
Copyright (c) Cutleast
"""

from functools import reduce
from threading import Lock
from typing import Optional, override

from PySide6.QtCore import QTimerEvent

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate, UpdateCallback
from cutleast_core_lib.core.utilities.singleton import Singleton, SingletonQObject
from cutleast_core_lib.ui.progress.display import ProgressDisplay


class MainProgressCoordinator(SingletonQObject, ProgressDisplay):
    """
    Singleton object that delegates the progress of primary processes in an app to any
    number of progress displays and update callbacks.
    """

    __displays: list[ProgressDisplay]
    __callbacks: list[UpdateCallback]

    __lock: Lock
    __pending_main_updates: list[ProgressUpdate]
    __main_update_timer_id: Optional[int]

    @override
    def __init__(self, *, replace_existing_instance: bool = False) -> None:
        super().__init__()
        Singleton.__init__(self, replace_existing_instance=replace_existing_instance)

        self.__displays = []
        self.__callbacks = []

        self.__lock = Lock()
        self.__pending_main_updates = []
        self.__main_update_timer_id = self.startTimer(ProgressDisplay.UPDATE_INTERVAL)

    def add_display(self, display: ProgressDisplay) -> None:
        """
        Adds a progress display to the coordinator.

        Args:
            display (ProgressDisplay): The display to add.
        """

        self.__displays.append(display)

    def remove_display(self, display: ProgressDisplay) -> None:
        """
        Removes a progress display from the coordinator.

        Args:
            display (ProgressDisplay): The display to remove.
        """

        self.__displays.remove(display)

    def add_update_callback(self, callback: UpdateCallback) -> None:
        """
        Adds a callable that is called when the main progress is updated.

        Args:
            callback (UpdateCallback): The callback to add.
        """

        self.__callbacks.append(callback)

    def remove_update_callback(self, callback: UpdateCallback) -> None:
        """
        Removes a callable that is called when the main progress is updated.

        Args:
            callback (UpdateCallback): The callback to remove.
        """

        self.__callbacks.remove(callback)

    @override
    def updateMainProgress(self, payload: ProgressUpdate) -> None:
        for display in self.__displays:
            display.updateMainProgress(payload)

        self.__pending_main_updates.append(payload)

    @override
    def timerEvent(self, event: QTimerEvent, /) -> None:
        super().timerEvent(event)

        if event.timerId() == self.__main_update_timer_id:
            self.__call_update_callbacks()

    def __call_update_callbacks(self) -> None:
        with self.__lock:
            if self.__pending_main_updates:
                payload: ProgressUpdate = reduce(
                    ProgressUpdate.update, self.__pending_main_updates
                )
                self.__pending_main_updates.clear()

                for callback in self.__callbacks:
                    callback(payload)

    @override
    def updateProgress(self, progress_id: int, payload: ProgressUpdate) -> None:
        for display in self.__displays:
            display.updateProgress(progress_id, payload)

    @override
    def cancel(self) -> None:
        for display in self.__displays:
            display.cancel()

    @override
    def removeProgress(self, progress_id: int) -> None:
        for display in self.__displays:
            display.removeProgress(progress_id)

    @override
    def clearProgressBars(self) -> None:
        for display in self.__displays:
            display.clearProgressBars()
