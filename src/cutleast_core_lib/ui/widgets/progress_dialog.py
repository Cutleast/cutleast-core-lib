"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Generic, Optional, TypeVar, override

import comtypes.client as cc
from PySide6.QtCore import QCoreApplication, Qt, QTimerEvent, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.datetime import format_duration
from cutleast_core_lib.core.utilities.exceptions import format_exception
from cutleast_core_lib.core.utilities.exe_info import get_current_path
from cutleast_core_lib.core.utilities.thread import Thread
from cutleast_core_lib.core.utilities.truncate import TruncateMode, truncate_string
from cutleast_core_lib.ui.widgets.section_area_widget import SectionAreaWidget
from cutleast_core_lib.ui.widgets.smooth_scroll_area import SmoothScrollArea

try:
    cc.GetModule(f"{get_current_path()}/res/TaskbarLib.tlb")

    import comtypes.gen.TaskbarLib as tbl  # type: ignore # noqa: E402

    taskbar = cc.CreateObject(
        "{56FDF344-FD6D-11d0-958A-006097C9A090}", interface=tbl.ITaskbarList3
    )
except Exception as ex:
    print(format_exception(ex))
    print("WARNING: No taskbar progress API available: see exception above")
    taskbar = None


TBL_DETERMINATE: int = 0x1
TBL_INDETERMINATE: int = 0x2

T = TypeVar("T")
V = TypeVar("V")


class ProgressDialog(QDialog, Generic[T]):
    """
    Custom QProgressDialog featuring a main progress bar and a collapsible section for
    additional progress bars (e.g. for worker threads).
    """

    class ProgressWidget(QWidget):
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

        def currentValue(self) -> int:
            return self.__pbar.value()

        def currentMax(self) -> int:
            return self.__pbar.maximum()

    __update_signal = Signal(int, ProgressUpdate)
    __update_main_signal = Signal(ProgressUpdate)

    __start_time: Optional[float] = None
    __timer_id: Optional[int] = None
    __thread: Thread[T]

    __tbprogress_hwnd: Optional[int] = None

    __vlayout: QVBoxLayout
    __section_area: SectionAreaWidget
    __additional_progress_vlayout: QVBoxLayout

    __main_progress: ProgressWidget
    __progress_widgets: dict[int, ProgressWidget]

    __max_height: Optional[int] = None

    log: logging.Logger = logging.getLogger("ProgressDialog")

    def __init__(
        self, func: Callable[[ProgressDialog[T]], T], parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)

        self.__tbprogress_hwnd = self.winId()

        # force focus
        self.setModal(True)

        self.__thread = Thread(target=lambda: func(self), parent=self)
        self.__thread.finished.connect(self.__on_finished)

        self.__init_ui()

        self.__update_main_signal.connect(self.__update_main_progress)
        self.__update_signal.connect(self.__update_progress)
        self.__section_area.toggled.connect(self.__on_section_toggled)

        self.__on_section_toggled(False)

    def __init_ui(self) -> None:
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedWidth(600)
        self.setMaximumHeight(400)

        self.__vlayout = QVBoxLayout(self)
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__vlayout)

        self.__main_progress = ProgressDialog.ProgressWidget()

        scroll_area = SmoothScrollArea()
        scroll_area.setWidgetResizable(True)
        additional_progress_widget = QWidget()
        additional_progress_widget.setContentsMargins(0, 0, 0, 0)
        self.__additional_progress_vlayout = QVBoxLayout()
        self.__additional_progress_vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__additional_progress_vlayout.setContentsMargins(0, 0, 0, 0)
        additional_progress_widget.setLayout(self.__additional_progress_vlayout)
        scroll_area.setWidget(additional_progress_widget)

        self.__section_area = SectionAreaWidget(
            self.__main_progress,
            scroll_area,
            toggle_position=SectionAreaWidget.TogglePosition.Right,
            stretch_content=False,
        )
        self.__vlayout.addWidget(self.__section_area)

        self.__progress_widgets = {}

    def __on_section_toggled(self, toggled: bool) -> None:
        self.__section_area.adjustSize()

        new_height: int
        if self.__max_height is not None:
            new_height = min(self.__max_height, self.__section_area.sizeHint().height())
        else:
            new_height = self.__section_area.sizeHint().height()

        self.setFixedHeight(new_height)

    @override
    def setMaximumHeight(self, maxh: int) -> None:
        self.__max_height = maxh

    def updateMainProgress(self, payload: ProgressUpdate) -> None:
        """
        Updates the main progress bar with the given payload. This method is thread-safe.

        Args:
            payload (ProgressUpdate):
                The payload containing the updated display values.
        """

        self.__update_main_signal.emit(payload)

    def __update_main_progress(self, payload: ProgressUpdate) -> None:
        self.__main_progress.updateProgress(payload)

        if taskbar is not None and self.__tbprogress_hwnd is not None:
            if self.__main_progress.currentMax() == 0:
                taskbar.SetProgressState(self.__tbprogress_hwnd, TBL_INDETERMINATE)
            else:
                taskbar.SetProgressState(self.__tbprogress_hwnd, TBL_DETERMINATE)
                taskbar.SetProgressValue(
                    self.__tbprogress_hwnd,
                    self.__main_progress.currentValue(),
                    self.__main_progress.currentMax(),
                )

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

        self.__update_signal.emit(progress_id, payload)

    def __update_progress(self, progress_id: int, payload: ProgressUpdate) -> None:
        if progress_id not in self.__progress_widgets:
            pwidget = ProgressDialog.ProgressWidget()
            self.__additional_progress_vlayout.addWidget(pwidget)
            self.__progress_widgets[progress_id] = pwidget

        self.__progress_widgets[progress_id].updateProgress(payload)

    @override
    def timerEvent(self, event: QTimerEvent) -> None:
        """
        Callback for timer timeout that updates elapsed time in window title.
        """

        super().timerEvent(event)

        self.setWindowTitle(
            self.tr("Elapsed time:")
            + " "
            + format_duration(int(time.time() - (self.__start_time or time.time())))
        )

    def run(self) -> T:
        """
        Shows the dialog, executes the callable and blocks the main thread until the
        callable is done or the dialog is closed by the user in which case the
        callable's thread gets terminated and a ProcessIncompleteError gets raised.

        Returns:
            T: The callable's return value.
        """

        self.show()
        self.__thread.start()

        self.__start_time = time.time()
        self.__timer_id = self.startTimer(1000)

        super().exec()

        self.killTimer(self.__timer_id)
        self.__timer_id = None

        self.log.debug(
            f"Time taken: {format_duration(int(time.time() - self.__start_time))}"
        )

        # clear taskbar state
        if self.__tbprogress_hwnd is not None and taskbar is not None:
            taskbar.SetProgressState(self.__tbprogress_hwnd, 0x0)

        result: T | Exception = self.__thread.get_result()

        if isinstance(result, Exception):
            raise result

        return result

    def __on_finished(self) -> None:
        """
        Method that gets called when the worker thread is finished. It just closes the
        dialog and allows the run() method to continue.
        """

        self.accept()

    @override
    def closeEvent(self, event: QCloseEvent, confirmation: bool = False) -> None:
        if not confirmation:
            message_box = QMessageBox(self)
            message_box.setWindowTitle(self.tr("Cancel?"))
            message_box.setText(
                self.tr(
                    "Are you sure you want to cancel? This may have unwanted "
                    "consequences, depending on the current running process!"
                )
            )
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.No)
            message_box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            message_box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))

            # Reapply stylesheet as setDefaultButton() doesn't update the style by itself
            app: Optional[QCoreApplication] = QApplication.instance()
            if isinstance(app, QApplication):
                message_box.setStyleSheet(app.styleSheet())

            confirmation = message_box.exec() == QMessageBox.StandardButton.Yes

        if confirmation:
            if self.__thread.isRunning():
                self.log.critical("Terminating background thread...")
                self.__thread.terminate()
            super().closeEvent(event)
        elif event:
            event.ignore()


if __name__ == "__main__":
    import random
    import sys
    import time

    from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
    from cutleast_core_lib.ui.utilities.ui_mode import UIMode

    app = QApplication(sys.argv)
    IconProvider(UIMode.Dark, "#ffffff")

    def process(pdialog: ProgressDialog[int]) -> int:
        total = 10
        pdialog.updateMainProgress(
            ProgressUpdate(status_text="Starting main process...", value=0, maximum=0)
        )

        workers: dict[int, Thread[None]] = {}
        for i in range(3):
            wid = i + 1

            def worker_func(wid: int) -> None:
                for j in range(total):
                    time.sleep(random.randint(5, 20) / 10)
                    pdialog.updateProgress(
                        wid,
                        ProgressUpdate(
                            status_text=f"Worker {wid}: Step {j + 1}/{total}",
                            value=j + 1,
                            maximum=total,
                        ),
                    )

            pdialog.updateProgress(
                wid,
                ProgressUpdate(
                    status_text=f"Worker {wid}: Starting...", value=0, maximum=0
                ),
            )

            thread = Thread(target=lambda wid=wid: worker_func(wid))
            workers[wid] = thread
            thread.start()

        for i in range(total):
            time.sleep(1)
            pdialog.updateMainProgress(
                ProgressUpdate(
                    status_text=f"Main process: Step {i + 1}/{total}",
                    value=i + 1,
                    maximum=total,
                )
            )

        for thread in workers.values():
            thread.wait()

        for wid in workers:
            pdialog.updateProgress(
                wid,
                ProgressUpdate(
                    status_text=f"Worker {wid}: Finalizing...",
                    value=total,
                    maximum=total,
                ),
            )

        pdialog.updateMainProgress(
            ProgressUpdate(
                status_text="Finalizing main process...", value=total, maximum=total
            )
        )

        return 42

    ProgressDialog(process).run()
