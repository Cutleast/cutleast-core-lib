"""
Copyright (c) Cutleast
"""

from functools import reduce
from typing import Optional, override

from PySide6.QtCore import Qt, QTimerEvent, Signal, SignalInstance
from PySide6.QtWidgets import QVBoxLayout, QWidget

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.ui.widgets.section_area_widget import SectionAreaWidget
from cutleast_core_lib.ui.widgets.smooth_scroll_area import SmoothScrollArea

from .bar import ProgressBarWidget
from .display import ProgressDisplay


class ProgressWidget(QWidget, ProgressDisplay):
    """
    Widget for displaying and managing a main progress bar and multiple sub progress
    bars.
    """

    __cancel_requested = Signal()
    __update_signal = Signal(int, ProgressUpdate)
    __update_main_signal = Signal(ProgressUpdate)
    __remove_signal = Signal(int)
    __clear_signal = Signal()

    __update_timer_id: Optional[int] = None

    __vlayout: QVBoxLayout
    __section_area: SectionAreaWidget
    __additional_progress_vlayout: QVBoxLayout

    __main_progress: ProgressBarWidget
    __progress_widgets: dict[int, ProgressBarWidget]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        ProgressDisplay.__init__(self)

        self.__init_ui()

        self._update_main_signal.connect(self.__update_main_progress)
        self._update_signal.connect(self.__update_progress)
        self._remove_signal.connect(self.__remove_progress)
        self._clear_signal.connect(self.__clear_progress_bars)

    def __init_ui(self) -> None:
        self.setContentsMargins(0, 0, 0, 0)

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

    def __update_main_progress(self, payload: ProgressUpdate) -> None:
        self.__main_progress.updateProgress(payload)

    def __update_progress(self, progress_id: int, payload: ProgressUpdate) -> None:
        if progress_id not in self.__progress_widgets:
            pwidget = ProgressBarWidget()
            self.__additional_progress_vlayout.addWidget(pwidget)
            self.__progress_widgets[progress_id] = pwidget
            self.__section_area.setToggleButtonVisible(True)
            if not self.__section_area.isExpanded():
                self.__section_area.setExpanded(True)

        self.__progress_widgets[progress_id].updateProgress(payload)

    def __remove_progress(self, progress_id: int) -> None:
        if progress_id in self.__progress_widgets:
            with self._lock:
                # clear scheduled any update
                self._scheduled_updates.pop(progress_id, None)
                widget: ProgressBarWidget = self.__progress_widgets.pop(progress_id)

            widget.hide()
            self.__additional_progress_vlayout.removeWidget(widget)
            widget.deleteLater()
            self.__section_area.setToggleButtonVisible(len(self.__progress_widgets) > 0)
            if self.__section_area.isExpanded():
                self.__section_area.setExpanded(len(self.__progress_widgets) > 0)

    def __clear_progress_bars(self) -> None:
        for progress_id in self.__progress_widgets.copy():
            self.removeProgress(progress_id)

    @override
    def timerEvent(self, event: QTimerEvent) -> None:
        """
        Callback for timer timeout that updates elapsed time in window title.
        """

        super().timerEvent(event)

        match event.timerId():
            case self.__update_timer_id:
                self.__process_scheduled_updates()

    def __process_scheduled_updates(self) -> None:
        with self._lock:
            progress_ids: list[int] = list(self._scheduled_updates.keys())

        for progress_id in progress_ids:
            with self._lock:
                payloads: Optional[list[ProgressUpdate]] = self._scheduled_updates.pop(
                    progress_id, None
                )

            if payloads is not None:
                updated_payload: ProgressUpdate = reduce(
                    ProgressUpdate.update, payloads
                )

                self.__update_progress(progress_id, updated_payload)

    def startUpdateTimer(self) -> None:
        """
        Starts the update timer that process all progress updates in a fixed interval.
        """

        self.__update_timer_id = self.startTimer(ProgressDisplay.UPDATE_INTERVAL)

    def stopUpdateTimer(self) -> None:
        """
        Stops the update timer.
        """

        if self.__update_timer_id is not None:
            self.__update_timer_id = self.killTimer(self.__update_timer_id)

    @property
    @override
    def cancel_requested(self) -> SignalInstance:
        return self.__cancel_requested

    @property
    @override
    def _update_signal(self) -> SignalInstance:
        return self.__update_signal

    @property
    @override
    def _update_main_signal(self) -> SignalInstance:
        return self.__update_main_signal

    @property
    @override
    def _remove_signal(self) -> SignalInstance:
        return self.__remove_signal

    @property
    @override
    def _clear_signal(self) -> SignalInstance:
        return self.__clear_signal
