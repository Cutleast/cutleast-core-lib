"""
Copyright (c) Cutleast
"""

import logging
from abc import abstractmethod
from functools import reduce
from threading import Event, Lock
from typing import TYPE_CHECKING, Optional, override

from PySide6.QtCore import QObject, QTimerEvent, Signal
from PySide6.QtWidgets import QWidget

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.exceptions import TaskCancelledError

from .display import ProgressDisplay

if TYPE_CHECKING:
    from cutleast_core_lib.core.multithreading.progress_executor import ProgressExecutor


class BaseProgressWidget(ProgressDisplay):  # pyright: ignore[reportImplicitAbstractClass]
    """
    Base class for all widgets that implement the ProgressDisplay interface.

    This class does not inherit from QWidget directly to avoid inheritance conflicts in
    subclasses. Everything Qt-related is already handled by an internal helper QObject.
    """

    class _SignalHelper(QObject):
        """
        Helper QObject that holds the signals and the update timer.
        """

        cancel_requested = Signal()
        update_signal = Signal(int, ProgressUpdate)
        update_main_signal = Signal(ProgressUpdate)
        remove_signal = Signal(int)
        clear_signal = Signal()
        update_timer_signal = Signal()

        __update_timer_id: Optional[int] = None

        def start_update_timer(self, interval: int) -> None:
            if self.__update_timer_id is not None:
                return

            self.__update_timer_id = self.startTimer(interval)

        @override
        def timerEvent(self, event: QTimerEvent) -> None:
            super().timerEvent(event)

            if event.timerId() == self.__update_timer_id:
                self.update_timer_signal.emit()

        def stop_update_timer(self) -> None:
            if self.__update_timer_id is not None:
                self.__update_timer_id = self.killTimer(self.__update_timer_id)

    MAIN_PROGRESS_ID: int = -1
    """Constant progress ID for the main progress bar."""

    _lock: Lock
    _cancel_event: Event
    _scheduled_updates: dict[int, list[ProgressUpdate]]
    _signal_helper: _SignalHelper
    _progress_executor: Optional["ProgressExecutor"]

    log: logging.Logger

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        self._lock = Lock()
        self._cancel_event = Event()
        self._scheduled_updates = {}
        self._signal_helper = BaseProgressWidget._SignalHelper(parent)
        self._progress_executor = None

        self.log = logging.getLogger(self.__class__.__name__)

        self._signal_helper.update_main_signal.connect(self._update_main_progress)
        self._signal_helper.update_signal.connect(self._update_progress)
        self._signal_helper.remove_signal.connect(self._remove_progress)
        self._signal_helper.clear_signal.connect(self._clear_progress_bars)
        self._signal_helper.update_timer_signal.connect(self._process_scheduled_updates)

    def _start_update_timer(self) -> None:
        self._signal_helper.start_update_timer(ProgressDisplay.UPDATE_INTERVAL)

    def _stop_update_timer(self) -> None:
        self._signal_helper.stop_update_timer()

    @override
    def updateMainProgress(self, payload: ProgressUpdate) -> None:
        if self._cancel_event.is_set():
            raise TaskCancelledError

        self.updateProgress(BaseProgressWidget.MAIN_PROGRESS_ID, payload)

    @override
    def updateProgress(self, progress_id: int, payload: ProgressUpdate) -> None:
        if self._cancel_event.is_set():
            raise TaskCancelledError

        with self._lock:
            self._scheduled_updates.setdefault(progress_id, []).append(payload)

    def _process_scheduled_updates(self) -> None:
        with self._lock:
            updates_to_process: dict[int, list[ProgressUpdate]] = self._scheduled_updates
            self._scheduled_updates = {}

        for progress_id, payloads in updates_to_process.items():
            payload: ProgressUpdate = reduce(ProgressUpdate.update, payloads)
            if progress_id == BaseProgressWidget.MAIN_PROGRESS_ID:
                self._signal_helper.update_main_signal.emit(payload)
            else:
                self._signal_helper.update_signal.emit(progress_id, payload)

    @override
    def cancel(self) -> None:
        self._cancel_event.set()

        if self._progress_executor is not None:
            self._progress_executor.shutdown(wait=False, cancel_futures=True)

    @override
    def resetCancel(self) -> None:
        self._cancel_event.clear()

    @override
    def removeProgress(self, progress_id: int) -> None:
        self._signal_helper.remove_signal.emit(progress_id)

    @override
    def clearProgressBars(self) -> None:
        self._signal_helper.clear_signal.emit()

    @override
    def setProgressExecutor(self, executor: "ProgressExecutor") -> None:
        self._progress_executor = executor

    @abstractmethod
    def _update_main_progress(self, payload: ProgressUpdate) -> None:
        """
        Updates the main progress bar. This method does not need to be thread-safe.

        Args:
            payload (ProgressUpdate): The payload containing the updated display values.
        """

    @abstractmethod
    def _update_progress(self, progress_id: int, payload: ProgressUpdate) -> None:
        """
        Updates a progress bar for a specific progress ID. This method does not need to
        be thread-safe.

        Args:
            progress_id (int): ID of the progress to update the progress bar for.
            payload (ProgressUpdate): The payload containing the updated display values.
        """

    @abstractmethod
    def _remove_progress(self, progress_id: int) -> None:
        """
        Removes a progress bar for a specific progress ID. This method does not need to
        be thread-safe.

        Args:
            progress_id (int): ID of the progress to remove.
        """

    @abstractmethod
    def _clear_progress_bars(self) -> None:
        """
        Removes all progress bars but the main progress bar. This method does not need
        to be thread-safe.
        """
