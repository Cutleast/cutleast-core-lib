"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.truncate import TruncateMode, truncate_string


class ProgressBarWidget(QWidget):
    """
    Compound widget containing a label and a progress bar stacked vertically.
    """

    __vlayout: QVBoxLayout
    __label: QLabel
    __pbar: QProgressBar

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.__init_ui()

    def __init_ui(self) -> None:
        self.setContentsMargins(0, 0, 0, 0)

        self.__vlayout = QVBoxLayout()
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__vlayout)

        self.__label = QLabel()
        self.__label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.__vlayout.addWidget(self.__label)

        self.__pbar = QProgressBar()
        self.__pbar.setTextVisible(False)
        self.__vlayout.addWidget(self.__pbar)

    def updateProgress(self, payload: ProgressUpdate) -> None:
        """
        Updates the progress bar and label with the given payload.

        Args:
            payload (ProgressUpdate):
                The payload containing the updated display values.
        """

        if payload.status_text is not None:
            self.__label.setText(
                truncate_string(payload.status_text, 90, TruncateMode.Middle)
            )

        if payload.maximum is not None:
            self.__pbar.setMaximum(payload.maximum)

        if payload.value is not None:
            self.__pbar.setValue(payload.value)

    def currentProgress(self) -> ProgressUpdate:
        """
        Returns:
            ProgressUpdate:
                A ProgressUpdate object representing the currently displayed progress.
        """

        return ProgressUpdate(
            status_text=self.__label.text(),
            value=self.__pbar.value(),
            maximum=self.__pbar.maximum(),
        )
