"""
Copyright (c) Cutleast
"""

from enum import IntEnum

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.exceptions import format_exception
from cutleast_core_lib.core.utilities.exe_info import get_current_path
from cutleast_core_lib.core.utilities.typing_utils import not_none

tlb_path: str = f"{get_current_path()}/res/TaskbarLib.tlb"

try:
    import comtypes.client as cc

    cc.GetModule(tlb_path)

    import comtypes.gen.TaskbarLib as tbl  # type: ignore # noqa: E402

    tlb = cc.CreateObject(
        "{56FDF344-FD6D-11d0-958A-006097C9A090}", interface=tbl.ITaskbarList3
    )
except Exception as ex:
    print(format_exception(ex))
    print("DEBUG: TLB Path: " + tlb_path)
    print("WARNING: No taskbar progress API available: see exception above")
    tlb = None


class TaskbarProgressState(IntEnum):
    """Enum for the states of the taskbar progress."""

    NoProgress = 0x0
    """No progress is displayed. This is the default state."""

    Determinate = 0x1
    """The progress is determinate. A progress bar is displayed."""

    Indeterminate = 0x2
    """The progress is indeterminate. A processing indicator is displayed."""


class TaskbarProgressDisplay:
    """
    Wrapper for the Windows taskbar progress API to set the progress state and value of
    the taskbar button.

    If the TLB is not available, the methods will be no-ops.

    The consumer is responsible to avoid calling these methods too frequently, as they
    may freeze the Windows shell.
    """

    __hwnd: int

    def __init__(self, hwnd: int) -> None:
        """
        Args:
            hwnd (int): The handle of the window whose taskbar button should be updated.
        """

        self.__hwnd = hwnd

    def setProgressState(self, state: TaskbarProgressState) -> None:
        """
        Sets the progress state of the taskbar button.

        Args:
            state (TaskbarProgressState): The state to set.
        """

        if tlb is not None:
            tlb.SetProgressState(self.__hwnd, state.value)

    def setProgressValue(self, value: int, maximum: int) -> None:
        """
        Sets the progress value of the taskbar button.

        Args:
            value (int): The current progress value.
            maximum (int): The maximum progress value.
        """

        if tlb is not None:
            tlb.SetProgressValue(self.__hwnd, value, maximum)

    def clear(self) -> None:
        """
        Clears the progress state and value of the taskbar button.
        """

        if tlb is not None:
            tlb.SetProgressState(self.__hwnd, TaskbarProgressState.NoProgress.value)

    def updateProgress(self, progress_update: ProgressUpdate) -> None:
        """
        Updates the progress state and value of the taskbar button based on a
        ProgressUpdate.

        Args:
            progress_update (ProgressUpdate): The progress update to apply.
        """

        if not progress_update.is_determinate:
            self.setProgressState(TaskbarProgressState.Indeterminate)
        elif progress_update.is_completed:
            self.clear()
        else:
            self.setProgressState(TaskbarProgressState.Determinate)
            self.setProgressValue(
                value=not_none(progress_update.value),
                maximum=not_none(progress_update.maximum),
            )
