"""
Copyright (c) Cutleast
"""

from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate

if TYPE_CHECKING:
    from cutleast_core_lib.core.multithreading.progress_executor import ProgressExecutor


class ABCQtMeta(type(QWidget), ABCMeta):  # pyright: ignore[reportGeneralTypeIssues]
    """
    Combined metaclass for ABC + PySide6 Qt types to avoid metaclass conflicts.
    """


class ProgressDisplay(ABC, metaclass=ABCQtMeta):
    """
    Interface for all classes that can display and manage multiple progress bars including
    a main one.
    """

    UPDATE_INTERVAL: int = int(1_000 // 30)  # ~ 30 FPS
    """Interval in milliseconds for how often the progress bars should be updated."""

    TERMINATION_TIMEOUT: int = 1_000  # 1 second
    """Time in milliseconds to wait for the widget to terminate when cancelling."""

    @abstractmethod
    def updateMainProgress(self, payload: ProgressUpdate) -> None:
        """
        Updates the main progress bar with the given payload. This method is thread-safe.

        Args:
            payload (ProgressUpdate):
                The payload containing the updated display values.

        Raises:
            TaskCancelledError: If the cancel event has been set.
        """

    @abstractmethod
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

        Raises:
            TaskCancelledError: If the cancel event has been set.
        """

    @abstractmethod
    def cancel(self) -> None:
        """
        Sets a `threading.Event` that will raise a `TaskCancelledError` on the next
        update progress call.
        """

    @abstractmethod
    def removeProgress(self, progress_id: int) -> None:
        """
        Removes a progress bar by its progress ID from the widget. Does nothing if there
        is no progress bar for the specified ID. This method is thread-safe.

        Args:
            progress_id (int): ID of the progress to remove.
        """

    @abstractmethod
    def clearProgressBars(self) -> None:
        """
        Removes all progress bars but the main progress bar from the widget.
        """

    def setProgressExecutor(self, executor: "ProgressExecutor") -> None:
        """
        Sets a progress executor that will be shutdown when `cancel()` is called.

        Args:
            executor (ProgressExecutor): The progress executor.
        """
