"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import Qt, Signal, SignalInstance
from PySide6.QtWidgets import QHBoxLayout, QWidget

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.widgets.icon_button import IconButton

from .base import BaseProgressWidget
from .spinner import SpinnerWidget


class SpinnerDisplayWidget(BaseProgressWidget, QWidget):
    """
    Widget for displaying a main progress in a spinner widget and a cancel button.
    """

    _cancelled = Signal()

    __hlayout: QHBoxLayout
    __spinner_widget: SpinnerWidget
    __cancel_button: IconButton

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        QWidget.__init__(self, parent)
        super().__init__(parent)

        self.__init_ui()

        self.__cancel_button.clicked.connect(self.cancel)

        self._start_update_timer()

    def __init_ui(self) -> None:
        self.__hlayout = QHBoxLayout()
        self.__hlayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__hlayout)

        self.__spinner_widget = SpinnerWidget()
        self.__hlayout.addWidget(self.__spinner_widget)

        self.__cancel_button = IconButton()
        self.__cancel_button.setObjectName("cancel_button")
        self.__cancel_button.setProperty("transparent", True)
        self.__cancel_button.setToolTip(self.tr("Cancel"))
        IconProvider.bind_qta_icon(
            self.__cancel_button, self.__cancel_button.setIcon, "mdi6.cancel"
        )
        self.__hlayout.addWidget(self.__cancel_button)

    def setSpinnerSize(self, w: int, h: int) -> None:
        """
        Sets the size of the spinner. It is reset to the default size when the theme
        changes.

        Args:
            w (int): New width.
            h (int): New height.
        """

        self.__spinner_widget.setSpinnerSize(w, h)

    @property
    @override
    def cancelled(self) -> SignalInstance:
        return self._cancelled

    @override
    def _update_main_progress(self, payload: ProgressUpdate) -> None:
        self.__spinner_widget.updateProgress(payload)

    @override
    def _update_progress(self, progress_id: int, payload: ProgressUpdate) -> None:
        pass  # no subprogress widgets

    @override
    def _remove_progress(self, progress_id: int) -> None:
        pass  # no subprogress widgets

    @override
    def _clear_progress_bars(self) -> None:
        pass  # no subprogress widgets
