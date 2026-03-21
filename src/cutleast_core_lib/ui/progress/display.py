"""
Copyright (c) Cutleast
"""

import logging
from abc import ABCMeta, abstractmethod
from threading import Lock

from PySide6.QtCore import SignalInstance
from PySide6.QtWidgets import QWidget

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate


class ABCQtMeta(type(QWidget), ABCMeta):  # pyright: ignore[reportGeneralTypeIssues]
    """
    Combined metaclass for ABC + PySide6 Qt types to avoid metaclass conflicts.
    """


class ProgressDisplay(metaclass=ABCQtMeta):  # pyright: ignore[reportImplicitAbstractClass]
    """
    Base class for all widgets that can display and manage multiple progress bars
    including a main one.

    **Note:** This class does not inherit from QWidget on its own. This is to avoid
    inheritance conflicts in subclasses.
    """

    UPDATE_INTERVAL: int = int(1_000 // 30)  # ~ 30 FPS
    TERMINATION_TIMEOUT: int = 1_000  # 1 second

    _lock: Lock
    _scheduled_updates: dict[int, list[ProgressUpdate]]

    log: logging.Logger = logging.getLogger("ProgressDisplay")

    def __init__(self) -> None:
        self._lock = Lock()
        self._scheduled_updates = {}

    @property
    @abstractmethod
    def cancel_requested(self) -> SignalInstance:
        """Signal emitted when the user requested to cancel the process."""

    @property
    @abstractmethod
    def _update_signal(self) -> SignalInstance:
        """
        Internal signal emitted when the consumer requested to update a progress bar.

        Args:
            int: The id of the progress bar.
            ProgressUpdate: The payload containing the updated display values.
        """

    @property
    @abstractmethod
    def _update_main_signal(self) -> SignalInstance:
        """
        Internal signal emitted when the consumer requested to update the main progress bar.

        Args:
            ProgressUpdate: The payload containing the updated display values.
        """

    @property
    @abstractmethod
    def _remove_signal(self) -> SignalInstance:
        """
        Internal signal emitted when the consumer requested to remove a progress bar.

        Args:
            int: The id of the progress bar to remove.
        """

    @property
    @abstractmethod
    def _clear_signal(self) -> SignalInstance:
        """
        Internal signal emitted when the consumer requested to remove all progress bars but
        the main one.
        """

    def updateMainProgress(self, payload: ProgressUpdate) -> None:
        """
        Updates the main progress bar with the given payload. This method is thread-safe.

        Args:
            payload (ProgressUpdate):
                The payload containing the updated display values.
        """

        self._update_main_signal.emit(payload)

    def updateProgress(self, progress_id: int, payload: ProgressUpdate) -> None:
        """
        Updates the progress bar for a specific progress ID with the given payload.
        This method is thread-safe.

        Args:
            progress_id (int):
                ID of the progress to update the progress bar for. If there is no
                progress bar for the specified ID yet, a new one will be created.
            payload (ProgressUpdate):
                The payload containing the updated display values.
        """

        with self._lock:
            self._scheduled_updates.setdefault(progress_id, []).append(payload)

    def removeProgress(self, progress_id: int) -> None:
        """
        Removes a progress bar by its progress ID from the widget. Does nothing if there
        is no progress bar for the specified ID. This method is thread-safe.

        Args:
            progress_id (int): ID of the progress to remove.
        """

        self._remove_signal.emit(progress_id)

    def clearProgressBars(self) -> None:
        """
        Removes all progress bars but the main progress bar from the widget.
        """

        self._clear_signal.emit()
