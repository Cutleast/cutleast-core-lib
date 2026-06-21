"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import time
from typing import Callable, Generic, Optional, TypeVar, override

from PySide6.QtCore import QCoreApplication, Qt, QTimerEvent
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QVBoxLayout, QWidget

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.datetime import format_duration
from cutleast_core_lib.core.utilities.thread import Thread
from cutleast_core_lib.ui.widgets.section_area_widget import SectionAreaWidget
from cutleast_core_lib.ui.widgets.smooth_scroll_area import SmoothScrollArea

from .bar import ProgressBarWidget
from .base import BaseProgressWidget
from .display import ProgressDisplay
from .taskbar import TaskbarProgressDisplay

T = TypeVar("T")
V = TypeVar("V")


class ProgressDialog(BaseProgressWidget, QDialog, Generic[T]):
    """
    Custom QProgressDialog featuring a main progress bar and a collapsible section for
    additional progress bars (e.g. for worker threads).
    """

    __start_time: Optional[float] = None
    __titlebar_timer_id: Optional[int] = None
    __thread: Thread[T]

    __tb_display: TaskbarProgressDisplay

    __vlayout: QVBoxLayout
    __section_area: SectionAreaWidget
    __additional_progress_vlayout: QVBoxLayout

    __main_progress: ProgressBarWidget
    __progress_widgets: dict[int, ProgressBarWidget]

    __max_height: Optional[int] = None

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
        super().__init__(parent)

        self.__tb_display = TaskbarProgressDisplay(self.winId())

        # force focus
        self.setModal(True)

        self.__thread = Thread(target=lambda: func(self), parent=self)
        self.__thread.finished.connect(self.__on_finished)

        self.__init_ui()

        self.__section_area.toggled.connect(lambda _: self.__update_size())

        self.__update_size()

    def __init_ui(self) -> None:
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedWidth(600)
        self.setMaximumHeight(400)

        self.__vlayout = QVBoxLayout(self)
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__vlayout)

        self.__main_progress = ProgressBarWidget()

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
        self.__section_area.setToggleButtonVisible(False)
        self.__vlayout.addWidget(self.__section_area)

        self.__progress_widgets = {}

    def __update_size(self) -> None:
        self.__section_area.adjustSize()

        main_height: int = self.__main_progress.sizeHint().height()
        new_height: int = main_height + 15

        if self.__section_area.isExpanded():
            widget_count: int = len(self.__progress_widgets)
            new_height += main_height * widget_count
            new_height += self.__additional_progress_vlayout.spacing() * widget_count
            new_height += 10
        else:
            new_height += 5

        if self.__max_height is not None:
            new_height = min(self.__max_height, new_height)

        self.setFixedHeight(new_height)

    @override
    def setMaximumHeight(self, maxh: int) -> None:
        self.__max_height = maxh

    @override
    def _update_main_progress(self, payload: ProgressUpdate) -> None:
        self.__main_progress.updateProgress(payload)

        # we need the full progress update for the taskbar display
        cur_progress: ProgressUpdate = self.__main_progress.currentProgress()
        self.__tb_display.updateProgress(cur_progress)

    @override
    def _update_progress(self, progress_id: int, payload: ProgressUpdate) -> None:
        if progress_id not in self.__progress_widgets:
            pwidget = ProgressBarWidget()
            self.__additional_progress_vlayout.addWidget(pwidget)
            self.__progress_widgets[progress_id] = pwidget
            self.__section_area.setToggleButtonVisible(True)
            if self.__section_area.isExpanded():
                self.__update_size()
            else:
                self.__section_area.setExpanded(True)

        self.__progress_widgets[progress_id].updateProgress(payload)

    @override
    def _remove_progress(self, progress_id: int) -> None:
        if progress_id in self.__progress_widgets:
            with self._lock:
                # clear any scheduled update
                self._scheduled_updates.pop(progress_id, None)
                widget: ProgressBarWidget = self.__progress_widgets.pop(progress_id)

            widget.hide()
            self.__additional_progress_vlayout.removeWidget(widget)
            widget.deleteLater()
            self.__section_area.setToggleButtonVisible(len(self.__progress_widgets) > 0)
            if self.__section_area.isExpanded():
                self.__update_size()
                self.__section_area.setExpanded(len(self.__progress_widgets) > 0)

    @override
    def _clear_progress_bars(self) -> None:
        for progress_id in self.__progress_widgets.copy():
            self._remove_progress(progress_id)

    @override
    def timerEvent(self, event: QTimerEvent) -> None:
        """
        Callback for timer timeout that updates elapsed time in window title.
        """

        super().timerEvent(event)

        match event.timerId():
            case self.__titlebar_timer_id:
                self.__update_titlebar()

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
        self._start_update_timer()

        super().exec()

        self.__titlebar_timer_id = self.killTimer(self.__titlebar_timer_id)
        self._stop_update_timer()

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

            # Reapply stylesheet as setDefaultButton() doesn't update the style by itself
            app: Optional[QCoreApplication] = QApplication.instance()
            if isinstance(app, QApplication):
                message_box.setStyleSheet(app.styleSheet())

            confirmation = message_box.exec() == QMessageBox.StandardButton.Yes

        if confirmation:
            if self.__thread.isRunning():
                self.log.info("Requesting background thread to stop...")
                self.cancel()
                if not self.__thread.wait(ProgressDialog.TERMINATION_TIMEOUT):
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

    def process(pdisplay: ProgressDisplay) -> int:
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
