"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import (
    QAbstractAnimation,
    QByteArray,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum


class Toast(QWidget):
    """
    A simple animated toast notification that's displayed at the bottom of the screen.
    """

    MARGIN: int = 25
    """Margin to the screen borders."""

    class Position(LocalizedEnum):
        """Enum for the possible positions of the toast."""

        Top = "top"
        """The toast is displayed near the center of the top of the screen."""

        Bottom = "bottom"
        """The toast is displayed near the center of the bottom of the screen."""

        Left = "left"
        """The toast is displayed near the center of the left of the screen."""

        Right = "right"
        """The toast is displayed near the center of the right of the screen."""

        TopLeft = "top_left"
        """The toast is displayed near the top left of the screen."""

        TopRight = "top_right"
        """The toast is displayed near the top right of the screen."""

        BottomLeft = "bottom_left"
        """The toast is displayed near the bottom left of the screen."""

        BottomRight = "bottom_right"
        """The toast is displayed near the bottom right of the screen."""

        @override
        def get_localized_name(self) -> str:
            locs: dict[Toast.Position, str] = {
                Toast.Position.Top: QApplication.translate("Position", "Top"),
                Toast.Position.Bottom: QApplication.translate("Position", "Bottom"),
                Toast.Position.Left: QApplication.translate("Position", "Left"),
                Toast.Position.Right: QApplication.translate("Position", "Right"),
                Toast.Position.TopLeft: QApplication.translate("Position", "Top Left"),
                Toast.Position.TopRight: QApplication.translate(
                    "Position", "Top Right"
                ),
                Toast.Position.BottomLeft: QApplication.translate(
                    "Position", "Bottom Left"
                ),
                Toast.Position.BottomRight: QApplication.translate(
                    "Position", "Bottom Right"
                ),
            }

            return locs[self]

    __position: Position
    __offset_taskbar: bool

    __timer: QTimer
    __animation: QPropertyAnimation

    __frame: QFrame
    __icon_label: QLabel
    __text_label: QLabel

    def __init__(
        self,
        text: str,
        duration: int = 2,
        opacity: float = 1,
        anim_duration: float = 0.2,
        pos: Position = Position.Bottom,
        offset_taskbar: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            text (str): Text to display.
            duration (int, optional): Duration in seconds. Defaults to 2.
            opacity (float, optional): Window opacity. Defaults to 1 (100%).
            anim_duration (float, optional):
                Animation duration in seconds. Defaults to 0.2.
            pos (Position, optional):
                Position to show toast at. Defaults to Position.Bottom.
            offset_taskbar (bool, optional):
                Whether to account for the taskbar when positioning. Defaults to True.
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """

        super().__init__(parent)

        if parent is not None:
            parent.installEventFilter(self)

        self.installEventFilter(self)

        self.__timer = QTimer(self)
        self.__timer.setInterval(int((duration + anim_duration) * 1000))
        self.__timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.__timer.timeout.connect(self.hide)

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.__animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self.__animation.setDuration(int(anim_duration * 1000))
        self.__animation.setStartValue(0.0)
        self.__animation.setEndValue(opacity)
        self.__animation.valueChanged.connect(self.__set_opacity)

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vlayout)
        self.__frame = QFrame()
        self.__frame.setObjectName("content_frame")
        vlayout.addWidget(self.__frame)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__frame.setLayout(hlayout)

        self.__icon_label = QLabel()
        self.__icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hlayout.addWidget(self.__icon_label)

        self.__text_label = QLabel(text)
        self.__text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hlayout.addWidget(self.__text_label)

        self.setPosition(pos, offset_taskbar)
        self.__update_size()

        super().hide()

    def __set_opacity(self, opacity: float) -> None:
        self.setWindowOpacity(opacity)

        if opacity == 0.0:
            super().hide()

    @override
    def hide(self) -> None:
        """
        Hides the toast with animation.
        """

        self.__animation.setDirection(QAbstractAnimation.Direction.Backward)
        self.__animation.start()

        if self.__timer.isActive():
            self.__timer.stop()

    def setPosition(self, pos: Position, offset_taskbar: bool = True) -> None:
        """
        Sets the position of the toast.

        Args:
            pos (Position): New position.
            offset_taskbar (bool, optional):
                Whether to account for the taskbar when positioning. Defaults to True.
        """

        self.__position = pos
        self.__offset_taskbar = offset_taskbar
        self.__update_position()

    def __update_position(self) -> None:
        scr: QRect
        if self.__offset_taskbar:
            scr = QApplication.primaryScreen().availableGeometry()
        else:
            scr = QApplication.primaryScreen().geometry()

        point: QPoint = scr.center()
        x_offset: int = self.width() // 2 + Toast.MARGIN
        y_offset: int = self.height() // 2 + Toast.MARGIN

        match self.__position:
            case Toast.Position.Top:
                point.setY(y_offset)
            case Toast.Position.Bottom:
                point.setY(scr.height() - y_offset)
            case Toast.Position.Left:
                point.setX(x_offset)
            case Toast.Position.Right:
                point.setX(scr.width() - x_offset)
            case Toast.Position.TopLeft:
                point.setX(x_offset)
                point.setY(y_offset)
            case Toast.Position.TopRight:
                point.setX(scr.width() - x_offset)
                point.setY(y_offset)
            case Toast.Position.BottomLeft:
                point.setX(x_offset)
                point.setY(scr.height() - y_offset)
            case Toast.Position.BottomRight:
                point.setX(scr.width() - x_offset)
                point.setY(scr.height() - y_offset)

        rect: QRect = self.geometry()
        rect.moveCenter(point)
        self.setGeometry(rect)

    @override
    def show(self) -> None:
        """
        Shows the toast for the configured duration.
        """

        if self.__timer.isActive():
            self.__timer.stop()
            super().hide()

        self.__animation.setDirection(QAbstractAnimation.Direction.Forward)
        self.__animation.start()
        self.__timer.start()

        super().show()

    def __update_size(self) -> None:
        self.__text_label.adjustSize()
        self.__icon_label.adjustSize()
        self.__frame.adjustSize()

        self.setFixedSize(self.__frame.sizeHint())

    def setText(self, text: str) -> None:
        """
        Sets the text to display.

        Args:
            text (str): New text.
        """

        self.__text_label.setText(text)
        self.__update_size()

    def setIcon(self, icon: QIcon | QPixmap | str) -> None:
        """
        Sets the icon to display.

        Args:
            icon (QIcon | QPixmap | str): New icon.
        """

        if isinstance(icon, QIcon):
            icon = icon.pixmap(24, 24)
        elif isinstance(icon, str):
            icon = QIcon(icon).pixmap(24, 24)
        self.__icon_label.setPixmap(icon)
        self.__update_size()

    @override
    def eventFilter(self, object: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Resize:
            self.__update_position()

        return super().eventFilter(object, event)
