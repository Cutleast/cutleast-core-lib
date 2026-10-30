"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional, cast, override

from native_titlebar import NativeMainWindow
from PySide6.QtCore import QEvent, QMargins, Qt
from PySide6.QtWidgets import QApplication, QBoxLayout, QMenuBar, QWidget

from ..theme.manager import ThemeManager
from .elided_label import ElidedLabel

logging.getLogger("native_titlebar").setLevel(logging.WARNING)


class ExtendedMainWindow(NativeMainWindow):
    """
    Main window with a native title bar that hosts the menu bar in place of the
    left-aligned window title and displays the window title centered instead.
    """

    TITLE_BAR_LEFT_MARGIN: int = 36
    """
    Left margin of the title bar layout that keeps space for the window icon that is
    painted by the title bar.
    """

    TITLE_SPACING: int = 12
    """Minimum horizontal distance between the window title and other widgets."""

    __ready: bool

    __title_bar_layout: QBoxLayout
    __menu_bar: Optional[QMenuBar]
    __title_label: ElidedLabel

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            parent (Optional[QWidget], optional):
                Optional Qt parent. The window remains a top-level window. Defaults to
                None.

        Raises:
            NativeTitleBarError: If the native title bar could not be initialized.
        """

        # The base constructor already synchronizes the title bar layout and,
        # thereby, calls _update_titlebar_layout() before this class is set up.
        self.__ready = False

        super().__init__(parent)

        self.__menu_bar = None
        self.__title_bar_layout = cast(QBoxLayout, self.titleBar().layout())

        self.titleBar().setTitleVisible(False)
        self.__title_label = ElidedLabel(
            self.__get_displayed_title(), parent=self.titleBar()
        )
        self.__title_label.setObjectName("title_bar_title")
        self.__title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.__ready = True
        self._update_titlebar_layout()

        self.windowTitleChanged.connect(self.__on_window_title_changed)

    @override
    def menuBar(self) -> QMenuBar:
        if self.__menu_bar is None:
            self.setMenuBar(QMenuBar())

        return cast(QMenuBar, self.__menu_bar)

    @override
    def setMenuBar(self, menu_bar: QMenuBar, /) -> None:
        if menu_bar is self.__menu_bar:
            return

        if self.__menu_bar is not None:
            self.titleBar().removeWidget(self.__menu_bar)
            self.__menu_bar.deleteLater()

        self.__menu_bar = menu_bar
        alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        # The stretch pushes all other title bar widgets to the right while the left
        # alignment keeps the interactive area of the menu bar at its size hint.
        self.titleBar().addWidget(menu_bar, stretch=1, alignment=alignment)

        # add_widget() appends to the layout but the menu bar must stay in front of
        # title bar widgets that were added before.
        self.__title_bar_layout.removeWidget(menu_bar)
        self.__title_bar_layout.insertWidget(0, menu_bar, 1, alignment)

    @override
    def _update_titlebar_layout(self) -> None:
        if self.__ready:
            # The title bar resets its margins whenever the native metrics change,
            # which is always followed by a call to this method. The vertical margins
            # are removed as the menu bar would not fit into the title bar otherwise.
            margins: QMargins = self.__title_bar_layout.contentsMargins()
            self.__title_bar_layout.setContentsMargins(
                ExtendedMainWindow.TITLE_BAR_LEFT_MARGIN, 0, margins.right(), 0
            )

        super()._update_titlebar_layout()

        if self.__ready:
            self.__update_title_label()

    def __update_title_label(self) -> None:
        """
        Centers the window title in the title bar without overlapping the menu bar or
        other title bar widgets. If there is not enough space for exact centering, the
        title is moved towards the free space and elided if necessary.
        """

        title_bar_width: int = self.titleBar().width()
        center: int = title_bar_width // 2
        left_bound: int = ExtendedMainWindow.TITLE_BAR_LEFT_MARGIN
        right_bound: int = (
            title_bar_width - self.__title_bar_layout.contentsMargins().right()
        )

        for widget in self.titleBar().widgets():
            if widget.isHidden():
                continue

            if widget.geometry().center().x() < center:
                left_bound = max(
                    left_bound,
                    widget.geometry().right() + ExtendedMainWindow.TITLE_SPACING,
                )
            else:
                right_bound = min(
                    right_bound, widget.x() - ExtendedMainWindow.TITLE_SPACING
                )

        available_width: int = right_bound - left_bound
        self.__title_label.setVisible(available_width > 0)
        if available_width <= 0:
            return

        width: int = min(self.__title_label.sizeHint().width(), available_width)
        x: int = min(max(center - width // 2, left_bound), right_bound - width)
        self.__title_label.setGeometry(x, 0, width, self.titleBar().height())

    @override
    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)

        if self.__ready:
            self.__title_label.setProperty("active", self.isActiveWindow())
            ThemeManager.update_widget_styles(self.__title_label)

    def __get_displayed_title(self) -> str:
        return self.windowTitle() or QApplication.applicationDisplayName()

    def __on_window_title_changed(self, title: str) -> None:
        self.__title_label.setText(title or QApplication.applicationDisplayName())
        self.__update_title_label()
