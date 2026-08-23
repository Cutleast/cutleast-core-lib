"""
Copyright (c) Cutleast
"""

from typing import Any, Optional, override

import shiboken6
from PySide6.QtCore import QEvent, QModelIndex, QObject, QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QHelpEvent, QMouseEvent
from PySide6.QtWidgets import QAbstractItemView, QApplication, QWidget

from cutleast_core_lib.core.utilities.singleton import SingletonQObject

from ..widgets.tooltip_popup import TooltipPopup


class TooltipManager(SingletonQObject):
    """
    Replaces native application tooltips with a customizable popup widget.
    """

    HIDE_DELAY: int = 300
    """Delay in milliseconds before hiding a tooltip after leaving its source."""

    DEFAULT_DISPLAY_TIME: int = 10_000
    """Base display time in milliseconds for a tooltip without an explicit timeout."""

    DISPLAY_TIME_PER_CHARACTER: int = 40
    """Additional display time per character after the initial text length."""

    DISPLAY_TIME_THRESHOLD: int = 100
    """Text length after which the default display time increases."""

    __app: QApplication
    __popup: Optional[TooltipPopup]
    __hide_timer: QTimer
    __expire_timer: QTimer

    __source: Optional[QWidget]
    __source_rect: Optional[QRect]

    @override
    def __init__(self, app: QApplication) -> None:
        """
        Args:
            app (QApplication): Application whose tooltip events are handled.
        """

        super().__init__(app)

        self.__app = app
        self.__popup = TooltipPopup()
        self.__popup.destroyed.connect(self.__on_popup_destroyed)
        self.__source = None
        self.__source_rect = None

        self.__hide_timer = QTimer(self)
        self.__hide_timer.setSingleShot(True)
        self.__hide_timer.setInterval(TooltipManager.HIDE_DELAY)
        self.__hide_timer.timeout.connect(self.__hide_immediately)

        self.__expire_timer = QTimer(self)
        self.__expire_timer.setSingleShot(True)
        self.__expire_timer.timeout.connect(self.__hide_immediately)

        self.__app.installEventFilter(self)

    @property
    def is_visible(self) -> bool:
        """Whether the custom tooltip is currently visible."""

        return (
            self.__popup is not None
            and shiboken6.isValid(self.__popup)
            and self.__popup.isVisible()
        )

    @property
    def text(self) -> str:
        """The text currently displayed by the custom tooltip."""

        if (
            self.__popup is None
            or not shiboken6.isValid(self.__popup)
            or not self.is_visible
        ):
            return ""

        return self.__popup.text

    def show_text(
        self,
        position: QPoint,
        text: str,
        widget: Optional[QWidget] = None,
        rect: Optional[QRect] = None,
        msecs_display_time: int = -1,
    ) -> None:
        """
        Shows text in the custom tooltip.

        Args:
            position (QPoint): Global position that anchors the tooltip.
            text (str): Text to display. An empty string hides the tooltip.
            widget (Optional[QWidget], optional):
                Widget associated with the tooltip. Defaults to `None`.
            rect (Optional[QRect], optional):
                Source area in widget coordinates that keeps the tooltip visible.
                Defaults to `None`.
            msecs_display_time (int, optional):
                Explicit display time in milliseconds. A value less than or equal to `0`
                uses Qt's text-length-based default. Defaults to `-1`.

        Raises:
            ValueError: When a source area is supplied without an associated widget.
        """

        if not text:
            self.hide_text()
            return

        if rect is not None and widget is None:
            raise ValueError("A tooltip source rectangle requires an associated widget.")

        same_tooltip: bool = (
            self.is_visible
            and self.__popup is not None
            and shiboken6.isValid(self.__popup)
            and self.__popup.text == text
            and self.__source is widget
            and self.__source_rect == rect
        )
        self.__hide_timer.stop()
        self.__expire_timer.stop()
        self.__source = widget
        self.__source_rect = QRect(rect) if rect is not None else None

        if widget is not None:
            widget.destroyed.connect(self.__on_source_destroyed)

        if (
            not same_tooltip
            and self.__popup is not None
            and shiboken6.isValid(self.__popup)
        ):
            self.__popup.show_text(position, text, widget)

        display_time: int = (
            msecs_display_time
            if msecs_display_time > 0
            else (
                TooltipManager.DEFAULT_DISPLAY_TIME
                + TooltipManager.DISPLAY_TIME_PER_CHARACTER
                * max(0, len(text) - TooltipManager.DISPLAY_TIME_THRESHOLD)
            )
        )
        self.__expire_timer.start(display_time)

    def hide_text(self) -> None:
        """
        Hides the custom tooltip after Qt's normal leave delay.
        """

        if self.is_visible and not self.__hide_timer.isActive():
            self.__hide_timer.start()

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """
        Replaces applicable native tooltip events and tracks their lifecycle.

        Args:
            watched (QObject): Object receiving the event.
            event (QEvent): Event being processed.

        Returns:
            bool: `True` when the manager handled the event.
        """

        if event.type() == QEvent.Type.ToolTip and isinstance(event, QHelpEvent):
            return self.__handle_tooltip_event(watched, event)

        if self.__is_popup_object(watched):
            return super().eventFilter(watched, event)

        if self.__is_source_event(watched, event):
            return False

        if event.type() == QEvent.Type.Leave and watched is self.__source:
            self.hide_text()

        elif event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
            if self.__source_rect is not None and not self.__source_rect.contains(
                event.position().toPoint()
            ):
                self.hide_text()

        elif event.type() in {
            QEvent.Type.FocusOut,
            QEvent.Type.WindowDeactivate,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseButtonDblClick,
            QEvent.Type.Wheel,
        }:
            self.__hide_immediately()

        return super().eventFilter(watched, event)

    def __handle_tooltip_event(self, watched: QObject, event: QHelpEvent) -> bool:
        """
        Resolves and displays an application tooltip for a help event.

        Args:
            watched (QObject): Object receiving the tooltip event.
            event (QHelpEvent): Tooltip event with local and global positions.

        Returns:
            bool: `True` when a custom tooltip was displayed.
        """

        if not isinstance(watched, QWidget):
            return False

        text: str
        source: QWidget
        rect: QRect
        text, source, rect = self.__get_tooltip_data(watched, event.pos())
        if not text:
            return False

        self.show_text(event.globalPos(), text, source, rect)
        event.accept()
        return True

    def __get_tooltip_data(
        self, watched: QWidget, position: QPoint
    ) -> tuple[str, QWidget, QRect]:
        """
        Gets tooltip data from a widget or an item-view viewport.

        Args:
            watched (QWidget): Widget receiving the tooltip event.
            position (QPoint): Tooltip position in the widget's coordinates.

        Returns:
            tuple[str, QWidget, QRect]: Tooltip text, source widget and source area.
        """

        parent: Optional[QWidget] = watched.parentWidget()
        if isinstance(parent, QAbstractItemView) and watched is parent.viewport():
            index: QModelIndex = parent.indexAt(position)
            tooltip_data: Any = index.data(Qt.ItemDataRole.ToolTipRole)
            text: str = tooltip_data if isinstance(tooltip_data, str) else ""
            return text, watched, parent.visualRect(index)

        return watched.toolTip(), watched, watched.rect()

    def __is_source_event(self, watched: QObject, event: QEvent) -> bool:
        """
        Gets whether an event cannot affect the currently displayed tooltip.

        Args:
            watched (QObject): Object receiving the event.
            event (QEvent): Event being processed.

        Returns:
            bool: `True` when the event belongs to another object or no tooltip exists.
        """

        if not self.is_visible:
            return True

        if event.type() in {QEvent.Type.FocusOut, QEvent.Type.WindowDeactivate}:
            return not self.__is_source_window_object(watched)

        if event.type() in {
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseButtonDblClick,
            QEvent.Type.Wheel,
        }:
            return False

        return watched is not self.__source

    def __hide_immediately(self) -> None:
        """
        Hides the tooltip and clears its source state immediately.
        """

        self.__hide_timer.stop()
        self.__expire_timer.stop()
        if self.__popup is not None and shiboken6.isValid(self.__popup):
            self.__popup.hide()

        self.__source = None
        self.__source_rect = None

    @property
    def __popup_is_valid(self) -> bool:
        """
        Gets whether the popup's Qt object has not been destroyed.

        Returns:
            bool: `True` when the popup can still be used.
        """

        return self.__popup is not None and shiboken6.isValid(self.__popup)

    def __is_popup_object(self, watched: QObject) -> bool:
        """
        Gets whether an object belongs to the managed tooltip popup.

        Args:
            watched (QObject): Object receiving an application event.

        Returns:
            bool: `True` when the object is the popup or its window handle.
        """

        if not self.__popup_is_valid:
            return False

        if self.__popup is None:
            return False

        return watched is self.__popup or watched is self.__popup.windowHandle()

    def __is_source_window_object(self, watched: QObject) -> bool:
        """
        Gets whether an object belongs to the current tooltip source window.

        Args:
            watched (QObject): Object receiving an application event.

        Returns:
            bool: `True` when the object belongs to the tooltip source window.
        """

        if self.__source is None:
            return False

        source_window: QWidget = self.__source.window()
        return watched is source_window or watched is source_window.windowHandle()

    def __on_popup_destroyed(self) -> None:
        """
        Clears the popup reference after Qt destroys the top-level window.
        """

        self.__popup = None

    def __on_source_destroyed(self) -> None:
        """
        Hides the tooltip when its currently tracked source is destroyed.
        """

        if self.sender() is self.__source:
            self.__hide_immediately()
