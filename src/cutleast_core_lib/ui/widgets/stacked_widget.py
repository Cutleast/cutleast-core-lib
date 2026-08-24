"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Optional, override

from PySide6.QtCore import QEasingCurve, QPoint, Qt, QVariantAnimation
from PySide6.QtGui import QMouseEvent, QPainter, QPaintEvent, QPalette, QPixmap
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QStackedWidget, QStyle, QStyleOption, QWidget


class StackedWidget(QStackedWidget):
    """
    Animated QStackedWidget.
    """

    class Transition(Enum):
        """
        Enum for the visual transition between stacked widgets.
        """

        Slide = "Slide"
        """Moves the current and next widgets in opposite directions."""

        Alpha = "Alpha"
        """Fades the next widget over the current widget."""

    class _TransitionOverlay(QOpenGLWidget):
        """
        Renders pane snapshots on an OpenGL framebuffer during a transition.
        """

        __parent: QWidget
        __current_pixmap: Optional[QPixmap]
        __next_pixmap: Optional[QPixmap]
        __current_start: QPoint
        __current_end: QPoint
        __next_start: QPoint
        __next_end: QPoint
        __transition: StackedWidget.Transition
        __progress: float

        def __init__(self, parent: QWidget) -> None:
            """
            Args:
                parent (QWidget): Parent stacked widget.
            """

            super().__init__(parent)

            self.__parent = parent
            self.__current_pixmap = None
            self.__next_pixmap = None
            self.__current_start = QPoint()
            self.__current_end = QPoint()
            self.__next_start = QPoint()
            self.__next_end = QPoint()
            self.__transition = StackedWidget.Transition.Slide
            self.__progress = 0.0

            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)
            self.setUpdateBehavior(QOpenGLWidget.UpdateBehavior.NoPartialUpdate)

        def setTransition(
            self,
            current_pixmap: QPixmap,
            next_pixmap: QPixmap,
            transition: StackedWidget.Transition,
            current_start: QPoint,
            current_end: QPoint,
            next_start: QPoint,
            next_end: QPoint,
        ) -> None:
            """
            Sets the snapshots and positions for a transition.

            Args:
                current_pixmap (QPixmap): Snapshot of the current pane.
                next_pixmap (QPixmap): Snapshot of the next pane.
                transition (Transition): Visual transition to render.
                current_start (QPoint): Initial position of the current pane.
                current_end (QPoint): Final position of the current pane.
                next_start (QPoint): Initial position of the next pane.
                next_end (QPoint): Final position of the next pane.
            """

            self.__current_pixmap = current_pixmap
            self.__next_pixmap = next_pixmap
            self.__current_start = current_start
            self.__current_end = current_end
            self.__next_start = next_start
            self.__next_end = next_end
            self.__transition = transition
            self.__progress = 0.0

            self.setGeometry(self.__parent.rect())
            self.show()
            self.raise_()
            self.update()

        def clearTransition(self) -> None:
            """
            Hides the overlay and releases the active pane snapshots.
            """

            self.hide()

            self.__current_pixmap = None
            self.__next_pixmap = None

        def setProgress(self, progress: float) -> None:
            """
            Sets the current animation progress.

            Args:
                progress (float): Animation progress from 0.0 to 1.0.
            """

            self.__progress = progress

            self.update()

        @override
        def paintGL(self) -> None:
            if self.__current_pixmap is None or self.__next_pixmap is None:
                return

            painter = QPainter(self)

            match self.__transition:
                case StackedWidget.Transition.Slide:
                    painter.drawPixmap(
                        self.__interpolate(self.__current_start, self.__current_end),
                        self.__current_pixmap,
                    )
                    painter.drawPixmap(
                        self.__interpolate(self.__next_start, self.__next_end),
                        self.__next_pixmap,
                    )

                case StackedWidget.Transition.Alpha:
                    painter.fillRect(
                        self.rect(),
                        self.__parent.palette().brush(QPalette.ColorRole.Window),
                    )
                    painter.setOpacity(1.0 - self.__progress)
                    painter.drawPixmap(self.__current_start, self.__current_pixmap)
                    painter.setOpacity(self.__progress)
                    painter.drawPixmap(self.__next_end, self.__next_pixmap)

        def __interpolate(self, start: QPoint, end: QPoint) -> QPoint:
            """
            Calculates an interpolated position.

            Args:
                start (QPoint): Initial position.
                end (QPoint): Final position.

            Returns:
                QPoint: Position at the current animation progress.
            """

            return QPoint(
                round(start.x() + (end.x() - start.x()) * self.__progress),
                round(start.y() + (end.y() - start.y()) * self.__progress),
            )

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

    __duration: int = 400
    __anim_curve: QEasingCurve.Type = QEasingCurve.Type.InOutCubic
    __orientation: Qt.Orientation
    __reverse: bool
    __transition: Transition
    __overlay: _TransitionOverlay
    __animation: Optional[QVariantAnimation]
    __finish_animation: Optional[Callable[[], None]]
    _active: bool = False

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

        self.__orientation = orientation
        self.__reverse = reverse
        self.__transition = StackedWidget.Transition.Slide
        self.__overlay = StackedWidget._TransitionOverlay(self)
        self.__animation = None
        self.__finish_animation = None

    def setOrientation(self, orientation: Qt.Orientation) -> None:
        """
        Sets the orientation used for automatic slide directions.

        Args:
            orientation (Qt.Orientation): Orientation of the slide animation.
        """

        self.__orientation = orientation

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

    def setTransition(self, transition: Transition) -> None:
        """
        Sets the visual transition used for widget changes.

        Args:
            transition (Transition): Visual transition to use.
        """

        self.__transition = transition

    def transition(self) -> Transition:
        """
        Returns the visual transition used for widget changes.

        Returns:
            Transition: Configured visual transition.
        """

        return self.__transition

    def cancelAnimation(self) -> None:
        """
        Completes the active animation immediately.
        """

        if self.__animation is not None:
            self.__animation.stop()

        if self.__finish_animation is not None:
            self.__finish_animation()

    def slideInIndex(
        self, index: int, direction: Direction = Direction.Automatic
    ) -> None:
        """
        Transitions into a widget of a given index with a given direction.

        Args:
            index (int): The index of the widget to slide into.
            direction (Direction, optional):
                The direction of the slide animation. Defaults to Direction.Automatic.
        """

        if index > (self.count() - 1):
            direction = (
                StackedWidget.Direction.TopToBottom
                if self.__orientation == Qt.Orientation.Vertical
                else StackedWidget.Direction.RightToLeft
            )
            index = index % self.count()
        elif index < 0:
            direction = (
                StackedWidget.Direction.BottomToTop
                if self.__orientation == Qt.Orientation.Vertical
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
        Transitions into a given widget with a given direction.

        Args:
            nextWidget (QWidget): The widget to slide into.
            direction (Direction, optional):
                The direction of the slide animation. Defaults to Direction.Automatic.
        """

        if self._active:
            self.cancelAnimation()

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
        next_widget.setGeometry(0, 0, x_offset, y_offset)
        next_widget.ensurePolished()
        next_widget.show()
        next_widget.hide()

        if direction == StackedWidget.Direction.Automatic:
            if current_index < next_index:
                direction = (
                    StackedWidget.Direction.TopToBottom
                    if self.__orientation == Qt.Orientation.Vertical
                    else StackedWidget.Direction.RightToLeft
                )
            else:
                direction = (
                    StackedWidget.Direction.BottomToTop
                    if self.__orientation == Qt.Orientation.Vertical
                    else StackedWidget.Direction.LeftToRight
                )

        if self.__reverse:
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

        self.__overlay.setTransition(
            pixmap_current,
            pixmap_next,
            self.__transition,
            point_current,
            QPoint(x_offset + point_current.x(), y_offset + point_current.y()),
            QPoint(-x_offset + point_next.x(), -y_offset + point_next.y()),
            point_next,
        )

        animation = QVariantAnimation(self)
        self.__animation = animation
        animation.setDuration(self.__duration)
        animation.setEasingCurve(self.__anim_curve)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)

        def on_animation_value_changed(value: object) -> None:
            """
            Updates the overlay for an animation progress value.

            Args:
                value (object): Current animation progress value.
            """

            self.__overlay.setProgress(float(value))  # pyright: ignore[reportArgumentType]

        def on_anim_finished() -> None:
            if self.__animation is not animation:
                return

            self.setCurrentIndex(next_index)
            current_widget.hide()
            current_widget.move(point_current)
            self._active = False
            self.__overlay.clearTransition()
            self.__animation = None
            self.__finish_animation = None
            animation.deleteLater()

        self.__finish_animation = on_anim_finished
        animation.valueChanged.connect(on_animation_value_changed)
        animation.finished.connect(on_anim_finished)
        animation.start()

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
        self.cancelAnimation()
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
