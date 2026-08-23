"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import QByteArray, QPoint, QPropertyAnimation, QRect, Qt
from PySide6.QtGui import QGuiApplication, QScreen
from PySide6.QtGui import Qt as QtG
from PySide6.QtWidgets import QFrame, QLabel, QLayout, QVBoxLayout, QWidget

from ..theme.manager import ThemeManager
from ..theme.models.theme import Theme
from ..utilities import apply_shadow


class TooltipPopup(QWidget):
    """
    A transparent top-level window used to display an application tooltip.
    """

    CURSOR_X_OFFSET: int = 2
    """Horizontal offset in pixels from the tooltip anchor position."""

    CURSOR_Y_OFFSET: int = 16
    """Vertical offset in pixels from the tooltip anchor position."""

    FADE_DURATION: int = 120
    """Duration in milliseconds of the tooltip fade transition."""

    __shadow_margin: int
    __hiding: bool

    __anchor_position: QPoint
    __source: Optional[QWidget]

    __content_frame: QFrame
    __text_label: QLabel
    __fade_animation: QPropertyAnimation

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__anchor_position = QPoint()
        self.__hiding = False
        self.__source = None

        self.setWindowFlag(Qt.WindowType.ToolTip, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.__init_ui()

        self.__fade_animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self.__fade_animation.setDuration(TooltipPopup.FADE_DURATION)
        self.__fade_animation.finished.connect(self.__on_fade_finished)

        self.__update_theme(ThemeManager.get().theme)
        ThemeManager.get().theme_changed.connect(self.__on_theme_changed)

    @property
    def text(self) -> str:
        """The text currently displayed by the tooltip."""

        return self.__text_label.text()

    def show_text(self, position: QPoint, text: str, source: Optional[QWidget]) -> None:
        """
        Displays tooltip text close to the supplied global position.

        Args:
            position (QPoint): Global position that anchors the tooltip.
            text (str): Text to display.
            source (Optional[QWidget]): Widget associated with the tooltip.
        """

        self.__anchor_position = QPoint(position)
        self.__source = source
        self.__text_label.setText(text)
        self.__text_label.setWordWrap(QtG.mightBeRichText(text))

        self.__update_size(position, source)
        self.move(self.__get_position(position, source))
        self.__start_fade_in()

    @override
    def hide(self) -> None:
        """
        Fades the tooltip out before hiding its window.
        """

        if not self.isVisible() or self.__hiding:
            return

        self.__hiding = True
        self.__fade_animation.stop()
        self.__fade_animation.setStartValue(self.windowOpacity())
        self.__fade_animation.setEndValue(0.0)
        self.__fade_animation.start()

    def __start_fade_in(self) -> None:
        """
        Shows the tooltip and fades it to full opacity.
        """

        self.__hiding = False
        self.__fade_animation.stop()
        if not self.isVisible():
            self.setWindowOpacity(0.0)
            super().show()

        self.__fade_animation.setStartValue(self.windowOpacity())
        self.__fade_animation.setEndValue(1.0)
        self.__fade_animation.start()

    def __on_fade_finished(self) -> None:
        """
        Hides the window after a completed fade-out.
        """

        if self.__hiding:
            super().hide()

    def __init_ui(self) -> None:
        """
        Initializes the popup widget hierarchy.
        """

        outer_vlayout = QVBoxLayout(self)
        outer_vlayout.setSpacing(0)

        self.__content_frame = QFrame(self)
        self.__content_frame.setObjectName("content_frame")
        outer_vlayout.addWidget(self.__content_frame)

        content_layout = QVBoxLayout(self.__content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.__text_label = QLabel(self.__content_frame)
        self.__text_label.setTextFormat(Qt.TextFormat.AutoText)
        self.__text_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        content_layout.addWidget(self.__text_label)

    def __update_size(self, position: QPoint, source: Optional[QWidget]) -> None:
        """
        Updates the popup size for its text and target screen.

        Args:
            position (QPoint): Global position that anchors the tooltip.
            source (Optional[QWidget]): Widget associated with the tooltip.
        """

        screen: Optional[QScreen] = QGuiApplication.screenAt(position)
        if screen is None and source is not None:
            screen = source.screen()

        if screen is not None:
            max_width: int = max(1, screen.geometry().width() - 2 * self.__shadow_margin)
            self.__text_label.setMaximumWidth(max_width)

        self.__content_frame.adjustSize()
        self.adjustSize()

    def __get_position(self, position: QPoint, source: Optional[QWidget]) -> QPoint:
        """
        Gets a screen-bounded popup position close to the tooltip anchor.

        Args:
            position (QPoint): Global position that anchors the tooltip.
            source (Optional[QWidget]): Widget associated with the tooltip.

        Returns:
            QPoint: The global position at which to show the tooltip.
        """

        screen: Optional[QScreen] = QGuiApplication.screenAt(position)
        if screen is None and source is not None:
            screen = source.screen()

        if screen is None:
            screen = QGuiApplication.primaryScreen()

        screen_geometry: QRect = screen.geometry()
        popup_position: QPoint = position + QPoint(
            TooltipPopup.CURSOR_X_OFFSET - self.__shadow_margin,
            TooltipPopup.CURSOR_Y_OFFSET - self.__shadow_margin,
        )

        if popup_position.x() + self.width() > screen_geometry.right() + 1:
            popup_position.setX(popup_position.x() - 4 - self.width())

        if popup_position.y() + self.height() > screen_geometry.bottom() + 1:
            popup_position.setY(popup_position.y() - 24 - self.height())

        popup_position.setX(
            min(
                max(popup_position.x(), screen_geometry.left()),
                screen_geometry.right() - self.width() + 1,
            )
        )
        popup_position.setY(
            min(
                max(popup_position.y(), screen_geometry.top()),
                screen_geometry.bottom() - self.height() + 1,
            )
        )

        return popup_position

    def __update_theme(self, theme: Theme) -> None:
        """
        Updates shadow settings supplied by the current theme.

        Args:
            theme (Theme): The theme supplying the shadow metrics and color.
        """

        self.__shadow_margin = theme.metrics.shadow_margin
        layout: Optional[QLayout] = self.layout()
        if layout is not None:
            layout.setContentsMargins(
                self.__shadow_margin,
                self.__shadow_margin,
                self.__shadow_margin,
                self.__shadow_margin,
            )

        apply_shadow(
            widget=self.__content_frame,
            size=theme.metrics.shadow_size,
            shadow_color=theme.resolve(theme.colors.shadow),
        )

    def __on_theme_changed(self, theme: Theme) -> None:
        """
        Updates the popup after the application theme changes.

        Args:
            theme (Theme): The newly applied application theme.
        """

        self.__update_theme(theme)

        if self.isVisible():
            self.__update_size(self.__anchor_position, self.__source)
            self.move(self.__get_position(self.__anchor_position, self.__source))
