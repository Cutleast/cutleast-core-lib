"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.ui.widgets.section_area_widget import SectionAreaWidget
from cutleast_core_lib.ui.widgets.smooth_scroll_area import SmoothScrollArea

from .bar import ProgressBarWidget
from .base import BaseProgressWidget


class ProgressWidget(BaseProgressWidget, QWidget):
    """
    Widget for displaying and managing a main progress bar and multiple sub progress
    bars.
    """

    __vlayout: QVBoxLayout
    __section_area: SectionAreaWidget
    __additional_progress_vlayout: QVBoxLayout

    __main_progress: ProgressBarWidget
    __progress_widgets: dict[int, ProgressBarWidget]
    __toggle_button_visible: bool = True

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        QWidget.__init__(self, parent)
        super().__init__(parent)

        self.__init_ui()

        self._start_update_timer()

    def __init_ui(self) -> None:
        self.setContentsMargins(0, 0, 0, 0)

        self.__vlayout = QVBoxLayout(self)
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__vlayout)

        self.__main_progress = ProgressBarWidget()

        scroll_area = SmoothScrollArea()
        scroll_area.setProperty("transparent", True)
        scroll_area.setWidgetResizable(True)
        additional_progress_widget = QWidget()
        additional_progress_widget.setProperty("transparent", True)
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

    @override
    def _update_main_progress(self, payload: ProgressUpdate) -> None:
        self.__main_progress.updateProgress(payload)

    @override
    def _update_progress(self, progress_id: int, payload: ProgressUpdate) -> None:
        if progress_id not in self.__progress_widgets:
            pwidget = ProgressBarWidget()
            self.__additional_progress_vlayout.addWidget(pwidget)
            self.__progress_widgets[progress_id] = pwidget
            self.__section_area.setToggleButtonVisible(self.__toggle_button_visible)
            if not self.__section_area.isExpanded():
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
            self.__section_area.setToggleButtonVisible(
                self.__toggle_button_visible and len(self.__progress_widgets) > 0
            )
            if self.__section_area.isExpanded():
                self.__section_area.setExpanded(len(self.__progress_widgets) > 0)

    @override
    def _clear_progress_bars(self) -> None:
        for progress_id in self.__progress_widgets.copy():
            self._remove_progress(progress_id)

    def setToggleButtonVisible(self, visible: bool) -> None:
        """
        Sets the visibility of the toggle button for the additional progress bars.

        Args:
            visible (bool): Whether the toggle button should be visible.
        """

        self.__toggle_button_visible = visible
        self.__section_area.setToggleButtonVisible(visible)
