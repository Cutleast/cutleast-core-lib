"""
Copyright (c) Cutleast
"""

from __future__ import annotations

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

    def update(self, new_update: ProgressUpdate) -> ProgressUpdate:
        """
        Creates a new progress update where the data of this one is updated with the
        data of a new one.

        Args:
            new_update (ProgressUpdate): New progress update.

        Returns:
            ProgressUpdate: The updated progress update.
        """

        status_text: Optional[str] = (
            new_update.status_text
            if new_update.status_text is not None
            else self.status_text
        )
        value: Optional[int] = (
            new_update.value if new_update.value is not None else self.value
        )
        maximum: Optional[int] = (
            new_update.maximum if new_update.maximum is not None else self.maximum
        )

        return ProgressUpdate(status_text=status_text, value=value, maximum=maximum)
