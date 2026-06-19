"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtCore import Signal
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.qt_res_provider import read_resource


class SpinnerWidget(QWidget):
    """
    Custom widget containing a loading spinner and a status text.
    """

    __update_signal = Signal(ProgressUpdate)

    __spinner: QSvgWidget
    __label: QLabel
    __last_text: str = ""

    @override
    def __init__(self) -> None:
        super().__init__()

        self.setMinimumWidth(24)

        self.__init_ui()

        self.__update_signal.connect(self.__update_progress)

    def __init_ui(self) -> None:
        self.setContentsMargins(0, 0, 0, 0)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hlayout)

        self.__spinner = QSvgWidget()
        svg = read_resource(":/icons/spinner.svg")
        svg = svg.replace(  # Apply accent color to spinner
            ' stroke="#ff0000" ',
            f' stroke="{self.palette().accent().color().name()}" ',
        ).encode()
        self.__spinner.load(svg)
        self.__spinner.setFixedSize(24, 24)
        hlayout.addWidget(self.__spinner)

        self.__label = QLabel()
        hlayout.addWidget(self.__label)

    def updateProgress(self, progress_update: ProgressUpdate) -> None:
        """
        Updates the progress of the spinner. This method is thread-safe.

        Args:
            progress_update (ProgressUpdate): The progress update to apply.
        """

        self.__update_signal.emit(progress_update)

    def __update_progress(self, progress_update: ProgressUpdate) -> None:
        text: str = (
            progress_update.status_text
            if progress_update.status_text is not None
            else self.__last_text
        )
        self.__last_text = text
        if (
            progress_update.value is not None
            and progress_update.maximum is not None
            and progress_update.maximum != 0
        ):
            text = f"({int((progress_update.value / progress_update.maximum) * 100)} %) "
            text += self.__last_text

        self.setText(text)

    def setSpinnerSize(self, w: int, h: int) -> None:
        """
        Sets the size of the spinner.

        Args:
            w (int): New width.
            h (int): New height.
        """

        self.__spinner.setFixedSize(w, h)

    def setText(self, text: str) -> None:
        """
        Sets the text of the spinner label.

        Args:
            text (str): New text.
        """

        self.__label.setText(text)
