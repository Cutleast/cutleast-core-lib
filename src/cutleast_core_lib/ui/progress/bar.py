"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressBar, QVBoxLayout, QWidget

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.ui.widgets.elided_label import ElidedLabel


class ProgressBarWidget(QWidget):
    """
    Compound widget containing a label and a progress bar stacked vertically.

    The label is automatically elided in the middle and the progress bar is
    indeterminate by default.
    """

    __vlayout: QVBoxLayout
    __label: ElidedLabel
    __pbar: QProgressBar

    @override
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.__init_ui()

    def __init_ui(self) -> None:
        self.setContentsMargins(0, 0, 0, 0)

        self.__vlayout = QVBoxLayout()
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__vlayout)

        self.__label = ElidedLabel(elide_mode=Qt.TextElideMode.ElideMiddle)
        self.__label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.__vlayout.addWidget(self.__label)

        self.__pbar = QProgressBar()
        self.__pbar.setTextVisible(False)
        self.__pbar.setValue(0)
        self.__pbar.setMaximum(0)
        self.__vlayout.addWidget(self.__pbar)

    def updateProgress(self, payload: ProgressUpdate) -> None:
        """
        Updates the progress bar and label with the given payload.

        Args:
            payload (ProgressUpdate):
                The payload containing the updated display values.
        """

        if payload.status_text is not None:
            self.__label.setText(payload.status_text)

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
