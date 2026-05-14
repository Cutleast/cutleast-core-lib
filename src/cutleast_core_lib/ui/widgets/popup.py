"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.utilities.position import Position
from PySide6.QtCore import (
    QAbstractAnimation,
    QByteArray,
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Popup(QWidget):
    """
    An absolutely positioned popup widget that slides into view over its parent.

    The popup is rendered as a child of its parent (not a top-level window), so it
    appears above the parent's content but remains clipped to the parent's bounds
    during the slide animation. Unlike `cutleast_core_lib.ui.widgets.toast.Toast`
    it is **not** transparent to mouse events and accepts arbitrary content via
    `setWidget()`.
    """

    MARGIN: int = 10
    """Margin to the parent borders in pixels."""

    _position: Position
    _anim_duration: int

    _timer: QTimer
    _animation: QPropertyAnimation

    _frame: QFrame
    _frame_layout: QVBoxLayout
    _dismiss_button: QPushButton

    _content_widget: Optional[QWidget]

    def __init__(
        self,
        pos: Position = Position.Bottom,
        timeout: int = 0,
        anim_duration: float = 0.3,
        show_dismiss: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            pos (Position, optional):
                Anchor position within the parent. Defaults to `Position.Bottom`.
            timeout (int, optional):
                Seconds after which the popup auto-hides. `0` disables the timeout.
                Defaults to `0`.
            anim_duration (float, optional):
                Slide-animation duration in seconds. Defaults to `0.3`.
            show_dismiss (bool, optional):
                Whether to show the dismiss button. Defaults to `True`.
            parent (Optional[QWidget], optional): Parent widget. Defaults to `None`.
        """

        super().__init__(parent)

        if parent is not None:
            parent.installEventFilter(self)

        self._position = pos
        self._anim_duration = int(anim_duration * 1000)
        self._content_widget = None

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        if timeout > 0:
            self._timer.setInterval(timeout * 1000)
            self._timer.timeout.connect(self.hide)

        self._animation = QPropertyAnimation(self, QByteArray(b"pos"))
        self._animation.setDuration(self._anim_duration)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.finished.connect(self.__on_animation_finished)

        self.__init_ui(show_dismiss)

    def __init_ui(self, show_dismiss: bool) -> None:
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        self.setLayout(outer_layout)

        self._frame = QFrame()
        self._frame.setObjectName("content_frame")
        outer_layout.addWidget(self._frame)

        self._frame_layout = QVBoxLayout()
        self._frame.setLayout(self._frame_layout)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        header_layout.addStretch()
        self._dismiss_button = QPushButton()
        self._dismiss_button.setIcon(IconProvider.get_qta_icon("mdi6.close"))
        self._dismiss_button.setObjectName("popup_dismiss_button")
        self._dismiss_button.setFixedSize(20, 20)
        self._dismiss_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._dismiss_button.clicked.connect(self.hide)
        header_layout.addWidget(self._dismiss_button)
        self._frame_layout.addLayout(header_layout)

        if not show_dismiss:
            self._dismiss_button.hide()

        super().hide()

    def __compute_geometry(self) -> tuple[QPoint, QPoint]:
        parent_widget: Optional[QWidget] = self.parentWidget()
        if parent_widget is None:
            return QPoint(0, 0), QPoint(0, 0)

        self.adjustSize()
        parent_rect: QRect = parent_widget.rect()
        w: int = self.width()
        h: int = self.height()
        m: int = Popup.MARGIN

        # Centre positions
        cx: int = parent_rect.width() // 2 - w // 2
        cy: int = parent_rect.height() // 2 - h // 2

        target: QPoint
        start: QPoint
        match self._position:
            case Position.Top:
                target = QPoint(cx, m)
                start = QPoint(cx, -h)
            case Position.Bottom:
                target = QPoint(cx, parent_rect.height() - h - m)
                start = QPoint(cx, parent_rect.height())
            case Position.Left:
                target = QPoint(m, cy)
                start = QPoint(-w, cy)
            case Position.Right:
                target = QPoint(parent_rect.width() - w - m, cy)
                start = QPoint(parent_rect.width(), cy)
            case Position.TopLeft:
                target = QPoint(m, m)
                start = QPoint(-w, m)
            case Position.TopRight:
                target = QPoint(parent_rect.width() - w - m, m)
                start = QPoint(parent_rect.width(), m)
            case Position.BottomLeft:
                target = QPoint(m, parent_rect.height() - h - m)
                start = QPoint(-w, parent_rect.height() - h - m)
            case Position.BottomRight:
                target = QPoint(
                    parent_rect.width() - w - m, parent_rect.height() - h - m
                )
                start = QPoint(parent_rect.width(), parent_rect.height() - h - m)

        return target, start

    def __on_animation_finished(self) -> None:
        if self._animation.direction() == QAbstractAnimation.Direction.Backward:
            super().hide()

    def setPosition(self, pos: Position) -> None:
        """
        Changes the anchor position.

        Args:
            pos (Position): New anchor position.
        """

        self._position = pos
        if self.isVisible():
            target, _ = self.__compute_geometry()
            self.move(target)

    def setWidget(self, widget: QWidget) -> None:
        """
        Sets the content widget displayed inside the popup.

        Replaces any previously set widget. The popup resizes itself to fit the
        new content.

        Args:
            widget (QWidget): Widget to display as content.
        """

        if self._content_widget is not None:
            self._frame_layout.removeWidget(self._content_widget)
            self._content_widget.setParent(None)

        self._content_widget = widget
        self._frame_layout.addWidget(widget)

        self.adjustSize()
        if self.isVisible():
            target, _ = self.__compute_geometry()
            self.move(target)

    def setDismissVisible(self, visible: bool) -> None:
        """
        Shows or hides the dismiss button.

        Args:
            visible (bool): `True` to show, `False` to hide.
        """

        self._dismiss_button.setVisible(visible)

    @override
    def show(self) -> None:
        """
        Slides the popup into view.

        If a timeout was configured the auto-hide timer is (re-)started.
        """

        # Stop any running animation / timer
        self._animation.stop()
        if self._timer.isActive():
            self._timer.stop()

        target, start = self.__compute_geometry()

        self.move(start)
        self.raise_()
        super().show()

        self._animation.setStartValue(start)
        self._animation.setEndValue(target)
        self._animation.setDirection(QAbstractAnimation.Direction.Forward)
        self._animation.start()

        if self._timer.interval() > 0:
            self._timer.start()

    @override
    def hide(self) -> None:
        """
        Slides the popup out of view, then hides it.
        """

        if self._timer.isActive():
            self._timer.stop()

        self._animation.stop()

        target, start = self.__compute_geometry()

        self._animation.setStartValue(start)
        self._animation.setEndValue(target)
        self._animation.setDirection(QAbstractAnimation.Direction.Backward)
        self._animation.start()

    @override
    def eventFilter(self, object: QObject, event: QEvent) -> bool:
        if object is self.parentWidget() and event.type() == QEvent.Type.Resize:
            if self.isVisible():
                target, _ = self.__compute_geometry()
                self.move(target)

        return super().eventFilter(object, event)
