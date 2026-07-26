"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from enum import Enum
from typing import Optional, override

from PySide6.QtCore import (
    QByteArray,
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    Qt,
    Signal,
)
from PySide6.QtGui import QMouseEvent, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import QLabel, QStackedWidget, QStyle, QStyleOption, QWidget


class StackedWidget(QStackedWidget):
    """
    Animated QStackedWidget.
    """

    class Direction(Enum):
        """
        Enum for the direction of the animation.
        """

        LeftToRight = "LeftToRight"
        """The animation will slide the widgets from left to right."""

        RightToLeft = "RightToLeft"
        """The animation will slide the widgets from right to left."""

        TopToBottom = "TopToBottom"
        """The animation will slide the widgets from top to bottom."""

        BottomToTop = "BottomToTop"
        """The animation will slide the widgets from bottom to top."""

        Automatic = "Automatic"
        """The animation will automatically determine the direction."""

    __duration: int = 750
    __anim_curve: QEasingCurve.Type = QEasingCurve.Type.InOutCubic
    __orientation: Qt.Orientation
    __reverse: bool
    _active: bool = False

    # Signals
    anim_finish_signal = Signal()
    anim_cancel_signal = Signal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        orientation: Qt.Orientation = Qt.Orientation.Vertical,
        reverse: bool = False,
    ) -> None:
        """
        Args:
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
            orientation (Qt.Orientation, optional):
                The orientation of the animation. Defaults to Qt.Orientation.Vertical.
            reverse (bool, optional):
                If the animation should be reversed. Defaults to False.
        """

        super().__init__(parent)

        self.orientation = orientation
        self.reverse = reverse

    def setDuration(self, duration: int) -> None:
        """
        Args:
            duration (int): The animation duration in milliseconds.
        """

        self.__duration = duration

    def setAnimationCurve(self, easingCurve: QEasingCurve.Type) -> None:
        """
        Args:
            easingCurve (QEasingCurve.Type): The animation easing curve.
        """

        self.__anim_curve = easingCurve

    def slideInIndex(
        self, index: int, direction: Direction = Direction.Automatic
    ) -> None:
        """
        Slides into a widget of a given index with a given direction.

        Args:
            index (int): The index of the widget to slide into.
            direction (Direction, optional):
                The direction of the slide animation. Defaults to Direction.Automatic.
        """

        if index > (self.count() - 1):
            direction = (
                StackedWidget.Direction.TopToBottom
                if self.orientation == Qt.Orientation.Vertical
                else StackedWidget.Direction.RightToLeft
            )
            index = index % self.count()
        elif index < 0:
            direction = (
                StackedWidget.Direction.BottomToTop
                if self.orientation == Qt.Orientation.Vertical
                else StackedWidget.Direction.LeftToRight
            )
            index = (index + self.count()) % self.count()

        widget: Optional[QWidget] = self.widget(index)
        if widget is not None:
            self.slideInWidget(widget, direction)

    def slideInWidget(
        self, nextWidget: QWidget, direction: Direction = Direction.Automatic
    ) -> None:
        """
        Slides into a given widget with a given direction.

        Args:
            nextWidget (QWidget): The widget to slide into.
            direction (Direction, optional):
                The direction of the slide animation. Defaults to Direction.Automatic.
        """

        if self._active:
            return

        self._active = True
        current_index: int = self.currentIndex()
        next_index: int = self.indexOf(nextWidget)
        current_widget: QWidget = self.currentWidget()
        next_widget: QWidget = nextWidget

        if current_index == next_index:
            self._active = False
            return

        x_offset: int = self.frameRect().width()
        y_offset: int = self.frameRect().height()
        nextWidget.setGeometry(0, 0, x_offset, y_offset)

        if direction == StackedWidget.Direction.Automatic:
            if current_index < next_index:
                direction = (
                    StackedWidget.Direction.TopToBottom
                    if self.orientation == Qt.Orientation.Vertical
                    else StackedWidget.Direction.RightToLeft
                )
            else:
                direction = (
                    StackedWidget.Direction.BottomToTop
                    if self.orientation == Qt.Orientation.Vertical
                    else StackedWidget.Direction.LeftToRight
                )

        if self.reverse:
            match direction:
                case StackedWidget.Direction.TopToBottom:
                    direction = StackedWidget.Direction.BottomToTop
                case StackedWidget.Direction.BottomToTop:
                    direction = StackedWidget.Direction.TopToBottom
                case StackedWidget.Direction.LeftToRight:
                    direction = StackedWidget.Direction.RightToLeft
                case StackedWidget.Direction.RightToLeft:
                    direction = StackedWidget.Direction.LeftToRight

        match direction:
            case StackedWidget.Direction.BottomToTop:
                x_offset = 0
                y_offset = -y_offset
            case StackedWidget.Direction.TopToBottom:
                x_offset = 0
            case StackedWidget.Direction.RightToLeft:
                x_offset = -x_offset
                y_offset = 0
            case StackedWidget.Direction.LeftToRight:
                y_offset = 0

        point_current: QPoint = current_widget.pos()
        point_next: QPoint = next_widget.pos()

        pixmap_current: QPixmap = current_widget.grab()
        pixmap_next: QPixmap = next_widget.grab()

        label_current = QLabel(self)
        label_next = QLabel(self)
        label_current.resize(current_widget.size())
        label_next.resize(next_widget.size())
        label_current.show()
        label_next.show()
        label_current.setPixmap(pixmap_current)
        label_next.setPixmap(pixmap_next)

        label_current.move(0, 0)
        label_next.move(point_next.x() - x_offset, point_next.y() - y_offset)

        anim_current = QPropertyAnimation(label_current, QByteArray(b"pos"))
        anim_next = QPropertyAnimation(label_next, QByteArray(b"pos"))
        anim_group = QParallelAnimationGroup()

        anim_current.setDuration(self.__duration)
        anim_next.setDuration(self.__duration)
        anim_current.setEasingCurve(self.__anim_curve)
        anim_next.setEasingCurve(self.__anim_curve)

        anim_current.setStartValue(point_current)
        anim_current.setEndValue(
            QPoint(x_offset + point_current.x(), y_offset + point_current.y())
        )

        anim_next.setStartValue(
            QPoint(-x_offset + point_next.x(), -y_offset + point_next.y())
        )
        anim_next.setEndValue(point_next)

        anim_group.addAnimation(anim_current)
        anim_group.addAnimation(anim_next)

        def on_anim_finished() -> None:
            self.setCurrentIndex(next_index)
            current_widget.hide()
            current_widget.move(point_current)
            self._active = False
            label_current.hide()
            label_next.hide()

        anim_group.finished.connect(on_anim_finished)
        anim_group.start()

        self.anim_cancel_signal.connect(
            lambda: (
                anim_group.setCurrentTime(self.__duration)
                if anim_group.currentTime() > 50
                else None
            )
        )

    def slideInNext(self) -> None:
        """
        Slides into the next widget.
        """

        self.slideInIndex(
            self.currentIndex() + 1 if self.currentIndex() < (self.count() - 1) else 0
        )

    def slideInPrev(self) -> None:
        """
        Slides into the previous widget.
        """

        self.slideInIndex(
            self.currentIndex() - 1 if self.currentIndex() > 0 else self.count() - 1
        )

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.anim_cancel_signal.emit()
        event.ignore()

    @override
    def paintEvent(self, arg__1: QPaintEvent) -> None:
        super().paintEvent(arg__1)

        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(
            QStyle.PrimitiveElement.PE_Widget, option, painter, self
        )
