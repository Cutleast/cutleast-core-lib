"""
Copyright (c) Cutleast
"""

from typing import Callable, Optional

from pydantic import BaseModel

UpdateCallback = Callable[["ProgressUpdate"], None]


def update(update_callback: Optional[UpdateCallback], arg: "ProgressUpdate") -> None:
    """
    Function to call a update callback or do nothing if it is None.

    Args:
        update_callback (Optional[UpdateCallback]): Update callback to call or None.
        arg (ProgressUpdate): Argument to pass to update callback.
    """

    if update_callback is not None:
        update_callback(arg)


class ProgressUpdate(BaseModel, frozen=True):
    """
    Payload for updating the progress of a single thread.
    """

    status_text: Optional[str] = None
    """
    Displayed status text of the thread. Overwrites the previous text if specified.
    """

    value: Optional[int] = None
    """
    Progress value of the thread. Overwrites the previous value if specified.
    """

    maximum: Optional[int] = None
    """
    Maximum progress value of the thread. Overwrites the previous maximum if specified.
    If the value is 0 (unknown), progress bars are set to indeterminate mode.
    """
