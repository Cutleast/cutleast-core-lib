"""
Copyright (c) Cutleast
"""

import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.widgets.tab_widget import TabWidget


class TestAnimatedTabBar(BaseTest):
    """
    Tests `ui.widgets.animated_tab_bar.AnimatedTabBar` in a `TabWidget`.
    """

    SHORT_TEXT: str = "Similar (1)"
    """Text of the first tab."""

    LONG_TEXT: str = "Related strings of the current string (12)"
    """Text of the second tab, which is a lot wider than the first one."""

    @pytest.fixture
    def tab_widget(self, qtbot: QtBot) -> TabWidget:
        """
        Creates a displayed tab widget with two tabs and a centered tab bar, which gets
        its width from the size hint of the tab bar.

        Args:
            qtbot (QtBot): Fixture for managing Qt widgets.

        Returns:
            TabWidget: Displayed tab widget with test tabs.
        """

        widget = TabWidget()
        widget.setTabBarAlignment(Qt.AlignmentFlag.AlignCenter)
        widget.resize(800, 300)
        widget.addTab(QLabel("First page"), TestAnimatedTabBar.SHORT_TEXT)
        widget.addTab(QLabel("Second page"), TestAnimatedTabBar.LONG_TEXT)
        qtbot.addWidget(widget)
        widget.show()
        qtbot.waitUntil(widget.isVisible)

        return widget

    @staticmethod
    def __wait_for_tab_bar(qtbot: QtBot, tab_widget: TabWidget) -> None:
        """
        Waits until the tab bar has the width of its tabs (or its minimum width) and all
        visible tabs are inside of it.

        Args:
            qtbot (QtBot): Fixture for managing Qt widgets.
            tab_widget (TabWidget): The tab widget to wait for.
        """

        tab_bar = tab_widget.tabBar()

        def check() -> None:
            visible_tabs: list[int] = [
                index for index in range(tab_bar.count()) if tab_bar.isTabVisible(index)
            ]
            tab_width: int = sum(
                tab_bar.tabSizeHint(index).width() for index in visible_tabs
            )

            assert tab_bar.width() == max(tab_width, tab_bar.minimumSizeHint().width())
            for index in visible_tabs:
                assert tab_bar.tabRect(index).left() >= 0
                assert tab_bar.tabRect(index).right() < tab_bar.width()

        qtbot.waitUntil(check)

    def test_size_hint_is_independent_of_layout(self, tab_widget: TabWidget) -> None:
        """
        Tests that the size hint is the sum of the visible tabs, no matter how wide the
        bar currently is.

        Args:
            tab_widget (TabWidget): The tab widget to test.
        """

        # given
        tab_bar = tab_widget.tabBar()
        tab_bar.setTabVisible(0, False)
        expected: QSize = tab_bar.tabSizeHint(1)

        # when
        tab_bar.resize(10, tab_bar.height())

        # then
        assert tab_bar.sizeHint().width() == expected.width()

    def test_grows_and_shrinks_with_visible_tabs(
        self, qtbot: QtBot, tab_widget: TabWidget
    ) -> None:
        """
        Tests that the tab bar follows its tabs when they get shown and hidden without
        any other notification to the layout.

        Args:
            qtbot (QtBot): Fixture for managing Qt widgets.
            tab_widget (TabWidget): The tab widget to test.
        """

        # given
        tab_bar = tab_widget.tabBar()
        tab_bar.setUsesScrollButtons(False)

        # when
        tab_bar.setTabVisible(0, False)
        TestAnimatedTabBar.__wait_for_tab_bar(qtbot, tab_widget)
        narrow_width: int = tab_bar.width()

        tab_bar.setTabVisible(0, True)
        TestAnimatedTabBar.__wait_for_tab_bar(qtbot, tab_widget)
        wide_width: int = tab_bar.width()

        # then
        assert wide_width > narrow_width
        assert wide_width >= sum(
            tab_bar.tabSizeHint(index).width() for index in range(tab_bar.count())
        )

    def test_grows_with_changed_tab_text(
        self, qtbot: QtBot, tab_widget: TabWidget
    ) -> None:
        """
        Tests that the tab bar follows its tabs when their text changes.

        Args:
            qtbot (QtBot): Fixture for managing Qt widgets.
            tab_widget (TabWidget): The tab widget to test.
        """

        # given
        tab_bar = tab_widget.tabBar()
        tab_bar.setTabVisible(1, False)
        TestAnimatedTabBar.__wait_for_tab_bar(qtbot, tab_widget)
        narrow_width: int = tab_bar.width()

        # when
        tab_bar.setTabText(0, TestAnimatedTabBar.LONG_TEXT)
        TestAnimatedTabBar.__wait_for_tab_bar(qtbot, tab_widget)

        # then
        assert tab_bar.width() > narrow_width

    def test_single_tab_is_drawn_inside_of_the_bar(
        self, qtbot: QtBot, tab_widget: TabWidget
    ) -> None:
        """
        Tests that a single tab has the same distance to the left and to the right edge
        of the bar. The stylesheet doesn't treat a single tab as the last tab, which
        used to remove its right margin and draw it over the edge of the bar.

        Args:
            qtbot (QtBot): Fixture for managing Qt widgets.
            tab_widget (TabWidget): The tab widget to test.
        """

        # given
        tab_bar = tab_widget.tabBar()
        tab_bar.setTabVisible(0, False)
        TestAnimatedTabBar.__wait_for_tab_bar(qtbot, tab_widget)
        selected_color: QColor = QColor.fromString(
            ThemeManager.get().theme.resolve(ThemeManager.get().theme.colors.primary_bg)
        )

        # when
        bar_image: QImage = tab_bar.grab().toImage()
        center_y: int = bar_image.height() // 2

        def distance_to_pill(from_left: bool) -> int:
            """
            Counts the pixels between the edge of the bar and the selected tab.

            Args:
                from_left (bool): Whether to count from the left or the right edge.

            Returns:
                int: The distance in pixels.
            """

            columns = range(bar_image.width())
            for distance, x in enumerate(columns if from_left else reversed(columns)):
                if bar_image.pixelColor(x, center_y) == selected_color:
                    return distance

            return bar_image.width()

        # then
        assert abs(distance_to_pill(True) - distance_to_pill(False)) <= 1
