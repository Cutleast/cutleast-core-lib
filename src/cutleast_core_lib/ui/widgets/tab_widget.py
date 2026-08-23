"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import QEasingCurve, QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QBoxLayout, QTabBar, QTabWidget, QWidget

from .stacked_widget import StackedWidget


class TabWidget(QWidget):
    """
    Tab widget that animates page changes with a :class:`StackedWidget`.
    """

    currentChanged = Signal(int)
    """
    Signal emitted when the current tab changes.

    Args:
        int: Index of the newly selected tab.
    """

    tabCloseRequested = Signal(int)
    """
    Signal emitted when the close button of a tab is clicked.

    Args:
        int: Index of the tab to close.
    """

    __layout: QBoxLayout
    __tab_bar: QTabBar
    __pane: StackedWidget
    __tab_position: QTabWidget.TabPosition

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__tab_position = QTabWidget.TabPosition.North

        self.__init_ui()

        self.__tab_bar.currentChanged.connect(self.__on_tab_changed)
        self.__tab_bar.tabCloseRequested.connect(self.tabCloseRequested.emit)
        self.__tab_bar.tabMoved.connect(self.__on_tab_moved)

    def __init_ui(self) -> None:
        """
        Initializes the user interface.
        """

        self.__layout = QBoxLayout(QBoxLayout.Direction.TopToBottom, self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(8)

        self.__tab_bar = QTabBar(self)
        self.__tab_bar.setDrawBase(False)

        self.__pane = StackedWidget(self, orientation=Qt.Orientation.Horizontal)
        self.setTransition(StackedWidget.Transition.Alpha)

        self.__layout.addWidget(self.__tab_bar)
        self.__layout.addWidget(self.__pane)

    def addTab(
        self, widget: QWidget, icon_or_text: QIcon | str, text: Optional[str] = None
    ) -> int:
        """
        Adds a tab containing a widget.

        Args:
            widget (QWidget): Widget to show in the tab.
            icon_or_text (QIcon | str): Icon or text displayed on the tab.
            text (Optional[str], optional): Text beside an icon. Defaults to None.

        Returns:
            int: Index of the added tab.
        """

        return self.insertTab(self.count(), widget, icon_or_text, text)

    def insertTab(
        self,
        index: int,
        widget: QWidget,
        icon_or_text: QIcon | str,
        text: Optional[str] = None,
    ) -> int:
        """
        Inserts a tab containing a widget.

        Args:
            index (int): Index where the tab is inserted.
            widget (QWidget): Widget to show in the tab.
            icon_or_text (QIcon | str): Icon or text displayed on the tab.
            text (Optional[str], optional): Text beside an icon. Defaults to None.

        Returns:
            int: Index of the inserted tab.
        """

        pane_index: int = self.__pane.insertWidget(index, widget)
        if isinstance(icon_or_text, QIcon):
            if text is None:
                raise TypeError("A tab icon requires tab text.")

            tab_index: int = self.__tab_bar.insertTab(pane_index, icon_or_text, text)

        else:
            if text is not None:
                raise TypeError("A text-only tab accepts exactly three arguments.")

            tab_index = self.__tab_bar.insertTab(pane_index, icon_or_text)

        return tab_index

    def removeTab(self, index: int) -> None:
        """
        Removes a tab without deleting its widget.

        Args:
            index (int): Index of the tab to remove.
        """

        widget: Optional[QWidget] = self.__pane.widget(index)
        if widget is not None:
            self.__pane.removeWidget(widget)

        self.__tab_bar.removeTab(index)

    def count(self) -> int:
        """
        Returns the number of tabs.

        Returns:
            int: Number of tabs.
        """

        return self.__tab_bar.count()

    def currentIndex(self) -> int:
        """
        Returns the index of the current tab.

        Returns:
            int: Index of the current tab.
        """

        return self.__tab_bar.currentIndex()

    def currentWidget(self) -> Optional[QWidget]:
        """
        Returns the widget shown by the current tab.

        Returns:
            Optional[QWidget]: Widget shown by the current tab.
        """

        return self.__pane.currentWidget()

    def widget(self, index: int) -> Optional[QWidget]:
        """
        Returns the widget at an index.

        Args:
            index (int): Index of the widget.

        Returns:
            Optional[QWidget]: Widget at the index.
        """

        return self.__pane.widget(index)

    def indexOf(self, widget: QWidget) -> int:
        """
        Returns the index of a widget.

        Args:
            widget (QWidget): Widget to find.

        Returns:
            int: Index of the widget, or -1 when it is absent.
        """

        return self.__pane.indexOf(widget)

    def setTabIcon(self, index: int, icon: QIcon) -> None:
        """
        Sets a tab icon.

        Args:
            index (int): Index of the tab.
            icon (QIcon): Icon to display.
        """

        self.__tab_bar.setTabIcon(index, icon)

    def tabIcon(self, index: int) -> QIcon:
        """
        Returns a tab icon.

        Args:
            index (int): Index of the tab.

        Returns:
            QIcon: Icon displayed by the tab.
        """

        return self.__tab_bar.tabIcon(index)

    def setTabText(self, index: int, text: str) -> None:
        """
        Sets the text of a tab.

        Args:
            index (int): Index of the tab.
            text (str): New tab text.
        """

        self.__tab_bar.setTabText(index, text)

    def tabText(self, index: int) -> str:
        """
        Returns the text of a tab.

        Args:
            index (int): Index of the tab.

        Returns:
            str: Text displayed by the tab.
        """

        return self.__tab_bar.tabText(index)

    def setTabToolTip(self, index: int, tool_tip: str) -> None:
        """
        Sets the tool tip of a tab.

        Args:
            index (int): Index of the tab.
            tool_tip (str): Tool tip to display.
        """

        self.__tab_bar.setTabToolTip(index, tool_tip)

    def tabToolTip(self, index: int) -> str:
        """
        Returns the tool tip of a tab.

        Args:
            index (int): Index of the tab.

        Returns:
            str: Tool tip displayed by the tab.
        """

        return self.__tab_bar.tabToolTip(index)

    def setTabEnabled(self, index: int, enabled: bool) -> None:
        """
        Enables or disables a tab.

        Args:
            index (int): Index of the tab.
            enabled (bool): Whether the tab should be enabled.
        """

        self.__tab_bar.setTabEnabled(index, enabled)

    def isTabEnabled(self, index: int) -> bool:
        """
        Returns whether a tab is enabled.

        Args:
            index (int): Index of the tab.

        Returns:
            bool: Whether the tab is enabled.
        """

        return self.__tab_bar.isTabEnabled(index)

    def setTabVisible(self, index: int, visible: bool) -> None:
        """
        Sets whether a tab is visible.

        Args:
            index (int): Index of the tab.
            visible (bool): Whether the tab should be visible.
        """

        self.__tab_bar.setTabVisible(index, visible)

    def isTabVisible(self, index: int) -> bool:
        """
        Returns whether a tab is visible.

        Args:
            index (int): Index of the tab.

        Returns:
            bool: Whether the tab is visible.
        """

        return self.__tab_bar.isTabVisible(index)

    def setIconSize(self, size: QSize) -> None:
        """
        Sets the size of tab icons.

        Args:
            size (QSize): Size of tab icons.
        """

        self.__tab_bar.setIconSize(size)

    def iconSize(self) -> QSize:
        """
        Returns the size of tab icons.

        Returns:
            QSize: Size of tab icons.
        """

        return self.__tab_bar.iconSize()

    def setElideMode(self, mode: Qt.TextElideMode) -> None:
        """
        Sets how tab text is elided.

        Args:
            mode (Qt.TextElideMode): Text elision mode.
        """

        self.__tab_bar.setElideMode(mode)

    def elideMode(self) -> Qt.TextElideMode:
        """
        Returns the text elision mode.

        Returns:
            Qt.TextElideMode: Text elision mode.
        """

        return self.__tab_bar.elideMode()

    def setDuration(self, duration: int) -> None:
        """
        Sets the duration of tab-change animations.

        Args:
            duration (int): Animation duration in milliseconds.
        """

        self.__pane.setDuration(duration)

    def setAnimationCurve(self, easing_curve: QEasingCurve.Type) -> None:
        """
        Sets the easing curve of tab-change animations.

        Args:
            easing_curve (QEasingCurve.Type): Easing curve of the animation.
        """

        self.__pane.setAnimationCurve(easing_curve)

    def setTransition(self, transition: StackedWidget.Transition) -> None:
        """
        Sets the visual transition used for tab changes.

        Args:
            transition (StackedWidget.Transition): Visual transition to use.
        """

        self.__pane.setTransition(transition)

    def transition(self) -> StackedWidget.Transition:
        """
        Returns the visual transition used for tab changes.

        Returns:
            StackedWidget.Transition: Configured visual transition.
        """

        return self.__pane.transition()

    def setCurrentIndex(self, index: int) -> None:
        """
        Selects a tab by its index.

        Args:
            index (int): Index of the tab to select.
        """

        self.__tab_bar.setCurrentIndex(index)

    def setCurrentWidget(self, widget: QWidget) -> None:
        """
        Selects the tab containing a widget.

        Args:
            widget (QWidget): Widget whose tab should be selected.
        """

        self.setCurrentIndex(self.indexOf(widget))

    def tabBar(self) -> QTabBar:
        """
        Returns the tab bar.

        Returns:
            QTabBar: Tab bar used by this widget.
        """

        return self.__tab_bar

    def pane(self) -> StackedWidget:
        """
        Returns the animated pane containing the tab widgets.

        Returns:
            StackedWidget: Pane containing the tab widgets.
        """

        return self.__pane

    def setTabPosition(self, position: QTabWidget.TabPosition) -> None:
        """
        Sets the position of the tab bar.

        Args:
            position (QTabWidget.TabPosition): Requested tab bar position.
        """

        self.__tab_position = position
        self.__layout.removeWidget(self.__tab_bar)
        self.__layout.removeWidget(self.__pane)

        self.__pane.setOrientation(
            Qt.Orientation.Horizontal
            if position in (QTabWidget.TabPosition.North, QTabWidget.TabPosition.South)
            else Qt.Orientation.Vertical
        )

        match position:
            case QTabWidget.TabPosition.North:
                self.__layout.setDirection(QBoxLayout.Direction.TopToBottom)
                self.__tab_bar.setShape(QTabBar.Shape.RoundedNorth)
                self.__layout.addWidget(self.__tab_bar)
                self.__layout.addWidget(self.__pane)

            case QTabWidget.TabPosition.South:
                self.__layout.setDirection(QBoxLayout.Direction.TopToBottom)
                self.__tab_bar.setShape(QTabBar.Shape.RoundedSouth)
                self.__layout.addWidget(self.__pane)
                self.__layout.addWidget(self.__tab_bar)

            case QTabWidget.TabPosition.West:
                self.__layout.setDirection(QBoxLayout.Direction.LeftToRight)
                self.__tab_bar.setShape(QTabBar.Shape.RoundedWest)
                self.__layout.addWidget(self.__tab_bar)
                self.__layout.addWidget(self.__pane)

            case QTabWidget.TabPosition.East:
                self.__layout.setDirection(QBoxLayout.Direction.LeftToRight)
                self.__tab_bar.setShape(QTabBar.Shape.RoundedEast)
                self.__layout.addWidget(self.__pane)
                self.__layout.addWidget(self.__tab_bar)

    def tabPosition(self) -> QTabWidget.TabPosition:
        """
        Returns the position of the tab bar.

        Returns:
            QTabWidget.TabPosition: Current tab bar position.
        """

        return self.__tab_position

    def setTabsClosable(self, closeable: bool) -> None:
        """
        Sets whether tabs display close buttons.

        Args:
            closeable (bool): Whether tabs should display close buttons.
        """

        self.__tab_bar.setTabsClosable(closeable)

    def tabsClosable(self) -> bool:
        """
        Returns whether tabs display close buttons.

        Returns:
            bool: Whether tabs display close buttons.
        """

        return self.__tab_bar.tabsClosable()

    def setMovable(self, movable: bool) -> None:
        """
        Sets whether users can move tabs.

        Args:
            movable (bool): Whether users can move tabs.
        """

        self.__tab_bar.setMovable(movable)

    def isMovable(self) -> bool:
        """
        Returns whether users can move tabs.

        Returns:
            bool: Whether users can move tabs.
        """

        return self.__tab_bar.isMovable()

    @override
    def setEnabled(self, enabled: bool) -> None:
        """
        Enables or disables the tab widget.

        Args:
            enabled (bool): Whether the widget should be enabled.
        """

        super().setEnabled(enabled)

        self.__tab_bar.setEnabled(enabled)
        self.__pane.setEnabled(enabled)

    def setTabBarAlignment(self, alignment: Qt.AlignmentFlag) -> None:
        """
        Sets the alignment of the tab bar.

        Args:
            alignment (Qt.AlignmentFlag): Alignment of the tab bar.
        """

        self.__layout.setAlignment(self.__tab_bar, alignment)

    def setSpacing(self, spacing: int) -> None:
        """
        Sets the spacing between the tab bar and the pane.

        Args:
            spacing (int): Spacing in pixels.
        """

        self.__layout.setSpacing(spacing)

    def __on_tab_changed(self, index: int) -> None:
        """
        Starts the matching pane animation after a tab-bar selection changes.

        Args:
            index (int): Index selected by the tab bar.
        """

        if index >= 0:
            self.__pane.cancelAnimation()
            self.__pane.slideInIndex(index)

        self.currentChanged.emit(index)

    def __on_tab_moved(self, from_index: int, to_index: int) -> None:
        """
        Keeps the pane order synchronized with a moved tab.

        Args:
            from_index (int): Previous tab index.
            to_index (int): New tab index.
        """

        widget: Optional[QWidget] = self.__pane.widget(from_index)
        if widget is not None:
            self.__pane.removeWidget(widget)
            self.__pane.insertWidget(to_index, widget)
