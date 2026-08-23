"""
Copyright (c) Cutleast
"""

import re
from typing import Optional, override

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QObject,
    QPoint,
    QRect,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QCursor, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QApplication, QRubberBand, QWidget


class WidgetInspector(QObject):
    """
    Temporarily lets the user select and describe a widget at runtime.
    """

    HOVER_UPDATE_INTERVAL: int = 40
    """Interval in milliseconds for updating the inspected widget highlight."""

    OBJECT_NAME_PATTERN: str = r"[A-Za-z_][\w-]*"
    """Regular expression for object names valid in a direct QSS selector."""

    inspected = Signal(str, str, str, str)
    """
    Signal emitted when a widget was inspected.

    Args:
        str: Widget object path.
        str: Suggested QSS selector.
        str: Widget class name.
        str: Widget object name.
    """

    cancelled = Signal()
    """Signal emitted when widget inspection was cancelled."""

    __active: bool

    __highlight: Optional[QRubberBand]
    __highlighted_widget: Optional[QWidget]

    __timer: QTimer

    @override
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.__active = False
        self.__highlight = None
        self.__highlighted_widget = None

        self.__timer = QTimer(self)
        self.__timer.setInterval(WidgetInspector.HOVER_UPDATE_INTERVAL)
        self.__timer.timeout.connect(self.__update_hover_target)

    @property
    def active(self) -> bool:
        """Whether an inspection is currently active."""

        return self.__active

    def start(self) -> None:
        """
        Starts inspecting. The next left click selects a widget.
        """

        if self.__active:
            return

        app = QApplication.instance()
        if not isinstance(app, QApplication):
            return

        self.__active = True
        app.installEventFilter(self)
        app.setOverrideCursor(Qt.CursorShape.CrossCursor)
        self.__timer.start()
        self.__update_hover_target()

    def stop(self, *, cancelled: bool = False) -> None:
        """
        Stops inspecting and removes all temporary UI state.

        Args:
            cancelled (bool, optional):
                Whether inspection was cancelled. Defaults to False.
        """

        if not self.__active:
            return

        app: Optional[QCoreApplication] = QApplication.instance()
        if isinstance(app, QApplication):
            app.removeEventFilter(self)
            app.restoreOverrideCursor()

        self.__active = False
        self.__timer.stop()
        self.__clear_highlight()
        if cancelled:
            self.cancelled.emit()

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not self.__active:
            return super().eventFilter(watched, event)

        if (
            event.type() == QEvent.Type.KeyPress
            and isinstance(event, QKeyEvent)
            and event.key() == Qt.Key.Key_Escape
        ):
            self.stop(cancelled=True)
            return True

        if event.type() == QEvent.Type.MouseButtonPress and isinstance(
            event, QMouseEvent
        ):
            if event.button() == Qt.MouseButton.LeftButton:
                target: Optional[QWidget] = self.__widget_at_cursor()
                if target is not None:
                    object_path: str = WidgetInspector.__object_path(target)
                    selector: str = WidgetInspector.__qss_selector(target)
                    class_name: str = target.metaObject().className()
                    object_name: str = target.objectName()
                    self.stop()
                    self.inspected.emit(object_path, selector, class_name, object_name)

                return True

            if event.button() == Qt.MouseButton.RightButton:
                self.stop(cancelled=True)
                return True

        return super().eventFilter(watched, event)

    @staticmethod
    def __object_path(widget: QWidget) -> str:
        """
        Builds a stable, readable QObject ancestry path for a widget.

        Args:
            widget (QWidget): Widget whose hierarchy should be described.

        Returns:
            str: Readable object hierarchy path.
        """

        parts: list[str] = []
        current: Optional[QWidget] = widget
        while current is not None:
            class_name: str = current.metaObject().className()
            object_name: str = current.objectName()
            parts.append(f"{class_name}#{object_name}" if object_name else class_name)
            current = current.parentWidget()

        return " > ".join(reversed(parts))

    @staticmethod
    def __qss_selector(widget: QWidget) -> str:
        """
        Returns the most useful QSS selector for a widget.

        Args:
            widget (QWidget): Widget for which to build a selector.

        Returns:
            str: Suggested QSS selector.
        """

        class_name: str = widget.metaObject().className()
        object_name: str = widget.objectName()
        if object_name:
            if re.fullmatch(WidgetInspector.OBJECT_NAME_PATTERN, object_name):
                return f"{class_name}#{object_name}"

            escaped_name: str = object_name.replace("\\", "\\\\").replace('"', '\\"')
            return f'{class_name}[objectName="{escaped_name}"]'

        named_parent: Optional[QWidget] = widget.parentWidget()
        while named_parent is not None and not named_parent.objectName():
            named_parent = named_parent.parentWidget()

        if named_parent is not None:
            return (
                f"{named_parent.metaObject().className()}#{named_parent.objectName()} "
                f"{class_name}"
            )

        return class_name

    def __update_hover_target(self) -> None:
        target: Optional[QWidget] = self.__widget_at_cursor()
        if target is self.__highlighted_widget:
            return

        self.__clear_highlight()
        if target is None:
            return

        window: QWidget = target.window()
        self.__highlight = QRubberBand(QRubberBand.Shape.Rectangle, window)
        self.__highlight.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        top_left = target.mapTo(window, QPoint(0, 0))
        self.__highlight.setGeometry(QRect(top_left, target.size()))
        self.__highlight.show()
        self.__highlighted_widget = target

    def __widget_at_cursor(self) -> Optional[QWidget]:
        widget: Optional[QWidget] = QApplication.widgetAt(QCursor.pos())
        if widget is self.__highlight:
            return self.__highlighted_widget

        return widget

    def __clear_highlight(self) -> None:
        if self.__highlight is not None:
            self.__highlight.hide()
            self.__highlight.deleteLater()

        self.__highlight = None
        self.__highlighted_widget = None
