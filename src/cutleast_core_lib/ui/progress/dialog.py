"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from threading import Lock
from typing import Generic, Optional, TypeVar, override

from PySide6.QtCore import Qt, QTimerEvent, SignalInstance
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.datetime import format_duration
from cutleast_core_lib.core.utilities.thread import Thread

from ..theme.manager import ThemeManager
from .display import ProgressDisplay
from .taskbar import TaskbarProgressDisplay
from .widget import ProgressWidget

T = TypeVar("T")
V = TypeVar("V")


class ProgressDialog(ProgressDisplay, QDialog, Generic[T]):
    """
    Custom QProgressDialog featuring a main progress bar and a collapsible section for
    additional progress bars (e.g. for worker threads).
    """

    __lock: Lock

    __start_time: Optional[float] = None
    __titlebar_timer_id: Optional[int] = None
    __thread: Thread[T]

    __tb_timer_id: Optional[int] = None
    __tb_display: TaskbarProgressDisplay

    __vlayout: QVBoxLayout
    __progress_widget: ProgressWidget
    __cancel_button: QPushButton

    __cur_progress: Optional[ProgressUpdate] = None
    __max_height: int = 400

    log: logging.Logger = logging.getLogger("ProgressDialog")

    def __init__(
        self, func: Callable[[ProgressDisplay], T], parent: Optional[QWidget] = None
    ) -> None:
        """
        Args:
            func (Callable[[ProgressDisplay], T]):
                Callable that gets executed in the background thread.
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        QDialog.__init__(self, parent)

        self.__lock = Lock()

        self.__tb_display = TaskbarProgressDisplay(self.winId())

        # force focus
        self.setModal(True)

        self.__thread = Thread(target=lambda: func(self), parent=self)
        self.__thread.finished.connect(self.__on_finished)

        self.__init_ui()
        self.__fit_height_to_content()

        self.__cancel_button.clicked.connect(self.close)

    def __init_ui(self) -> None:
        self.setMinimumWidth(600)

        self.__vlayout = QVBoxLayout(self)
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__vlayout)

        self.__progress_widget = ProgressWidget()
        self.__progress_widget.setToggleButtonVisible(False)
        self.__vlayout.addWidget(self.__progress_widget)

        self.__vlayout.addSpacing(5)

        self.__cancel_button = QPushButton(self.tr("Cancel"))
        self.__cancel_button.setProperty("transparent", True)
        self.__cancel_button.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            self.__cancel_button.sizePolicy().verticalPolicy(),
        )
        self.__vlayout.addWidget(
            self.__cancel_button, alignment=Qt.AlignmentFlag.AlignHCenter
        )

    @override
    def setMaximumHeight(self, maxh: int) -> None:
        self.__max_height = maxh

    @override
    def updateMainProgress(self, payload: ProgressUpdate) -> None:
        self.__progress_widget.updateMainProgress(payload)

        # we need the full progress update for the taskbar display
        with self.__lock:
            if self.__cur_progress is None:
                self.__cur_progress = payload
            else:
                self.__cur_progress = self.__cur_progress.update(payload)

    @override
    def updateProgress(self, progress_id: int, payload: ProgressUpdate) -> None:
        self.__progress_widget.updateProgress(progress_id, payload)

    @override
    def cancel(self) -> None:
        self.__progress_widget.cancel()

    @property
    @override
    def cancelled(self) -> SignalInstance:
        return self.__progress_widget.cancelled

    @override
    def resetCancel(self) -> None:
        self.__progress_widget.resetCancel()

    @override
    def removeProgress(self, progress_id: int) -> None:
        self.__progress_widget.removeProgress(progress_id)

    @override
    def clearProgressBars(self) -> None:
        self.__progress_widget.clearProgressBars()

    @override
    def timerEvent(self, event: QTimerEvent) -> None:
        """
        Callback for timer timeout that updates elapsed time in window title.
        """

        super().timerEvent(event)

        match event.timerId():
            case self.__titlebar_timer_id:
                self.__update_titlebar()
            case self.__tb_timer_id:
                with self.__lock:
                    if self.__cur_progress is not None:
                        self.__tb_display.updateProgress(self.__cur_progress)
                        self.__cur_progress = None

                self.__fit_height_to_content()

    def __fit_height_to_content(self) -> None:
        target_height: int = min(self.sizeHint().height(), self.__max_height)
        target_width: int = max(self.width(), self.minimumSizeHint().width())

        if self.height() != target_height or self.width() < target_width:
            self.setFixedSize(target_width, target_height)

    def __update_titlebar(self) -> None:
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
        self.__titlebar_timer_id = self.startTimer(1000)
        self.__tb_timer_id = self.startTimer(1000 // 10)  # 10 fps for taskbar updates

        super().exec()

        self.__progress_widget._stop_update_timer()  # pyright: ignore[reportPrivateUsage]
        self.__titlebar_timer_id = self.killTimer(self.__titlebar_timer_id)
        self.__tb_timer_id = self.killTimer(self.__tb_timer_id)

        self.log.debug(
            f"Time taken: {format_duration(int(time.time() - self.__start_time))}"
        )

        # clear taskbar state
        self.__tb_display.clear()

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

            ThemeManager.update_widget_styles(message_box)

            confirmation = message_box.exec() == QMessageBox.StandardButton.Yes

        if confirmation:
            if self.__thread.isRunning():
                self.log.info("Requesting background thread to stop...")
                self.cancel()
                if not self.__thread.wait(ProgressDisplay.TERMINATION_TIMEOUT):
                    self.log.critical(
                        "Background thread did not stop within timeout. Terminating..."
                    )
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

    def process(pdisplay: ProgressDisplay) -> int:  # noqa: D103
        total = 100000
        pdisplay.updateMainProgress(
            ProgressUpdate(status_text="Starting main process...", value=0, maximum=0)
        )

        workers: dict[int, Thread[None]] = {}
        for i in range(10):
            wid = i + 1

            def worker_func(wid: int) -> None:
                for j in range(total):
                    time.sleep(random.randint(5, 20) / 10000)
                    pdisplay.updateProgress(
                        wid,
                        ProgressUpdate(
                            status_text=f"Worker {wid}: Step {j + 1}/{total}",
                            value=j + 1,
                            maximum=total,
                        ),
                    )

                pdisplay.removeProgress(wid)

            pdisplay.updateProgress(
                wid,
                ProgressUpdate(
                    status_text=f"Worker {wid}: Starting...", value=0, maximum=0
                ),
            )

            thread = Thread(target=lambda wid=wid: worker_func(wid))
            workers[wid] = thread
            thread.start()

        for i in range(total):
            time.sleep(random.randint(5, 20) / 10000)
            pdisplay.updateMainProgress(
                ProgressUpdate(
                    status_text=f"Main process: Step {i + 1}/{total}",
                    value=i + 1,
                    maximum=total,
                )
            )

        for thread in workers.values():
            thread.wait()

        for wid in workers:
            pdisplay.updateProgress(
                wid,
                ProgressUpdate(
                    status_text=f"Worker {wid}: Finalizing...",
                    value=total,
                    maximum=total,
                ),
            )

        pdisplay.updateMainProgress(
            ProgressUpdate(
                status_text="Finalizing main process...", value=total, maximum=total
            )
        )

        return 42

    ProgressDialog(process).run()
