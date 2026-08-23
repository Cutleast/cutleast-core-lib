"""
Copyright (c) Cutleast
"""

import pytest
from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.stacked_widget import StackedWidget
from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget
from pytestqt.qtbot import QtBot


class TestStackedWidget(BaseTest):
    """
    Tests `ui.widgets.stacked_widget.StackedWidget`.
    """

    OVERLAY: tuple[str, type[QWidget]] = "overlay", QWidget
    """Identifier for accessing the private transition overlay field."""

    @pytest.fixture
    def stacked_widget(self, qtbot: QtBot) -> StackedWidget:
        """
        Creates a displayed stacked widget with three pages.

        Args:
            qtbot (QtBot): Fixture for managing Qt widgets.

        Returns:
            StackedWidget: Displayed stacked widget with test pages.
        """

        widget = StackedWidget()
        widget.resize(400, 300)
        widget.addWidget(QLabel("First page"))
        widget.addWidget(QLabel("Second page"))
        widget.addWidget(QLabel("Third page"))
        qtbot.addWidget(widget)
        widget.show()
        qtbot.waitUntil(widget.isVisible)

        return widget

    def test_default_transition_is_slide(self, stacked_widget: StackedWidget) -> None:
        """
        Tests that slide remains the default transition.

        Args:
            stacked_widget (StackedWidget): Stacked widget under test.
        """

        # then
        assert stacked_widget.transition() == StackedWidget.Transition.Slide

    def test_alpha_transition_completes_at_requested_widget(
        self, stacked_widget: StackedWidget, qtbot: QtBot
    ) -> None:
        """
        Tests that an alpha transition completes at the requested widget.

        Args:
            stacked_widget (StackedWidget): Stacked widget under test.
            qtbot (QtBot): Fixture for waiting on asynchronous Qt work.
        """

        # given
        stacked_widget.setTransition(StackedWidget.Transition.Alpha)
        stacked_widget.setDuration(1)

        # when
        stacked_widget.slideInIndex(1)

        # then
        qtbot.waitUntil(lambda: stacked_widget.currentIndex() == 1)
        assert stacked_widget.currentWidget() is stacked_widget.widget(1)
        overlay: QWidget = Utils.get_private_field(
            stacked_widget, *TestStackedWidget.OVERLAY
        )
        assert not overlay.isVisible()

    def test_alpha_transition_cancels_before_starting_next_transition(
        self, stacked_widget: StackedWidget, qtbot: QtBot
    ) -> None:
        """
        Tests that a second alpha transition deterministically replaces the first.

        Args:
            stacked_widget (StackedWidget): Stacked widget under test.
            qtbot (QtBot): Fixture for waiting on asynchronous Qt work.
        """

        # given
        stacked_widget.setTransition(StackedWidget.Transition.Alpha)
        stacked_widget.setDuration(200)

        # when
        stacked_widget.slideInIndex(1)
        stacked_widget.slideInIndex(2)

        # then
        qtbot.waitUntil(lambda: stacked_widget.currentIndex() == 2)
        assert stacked_widget.currentWidget() is stacked_widget.widget(2)

    def test_target_page_is_laid_out_before_alpha_snapshot(self, qtbot: QtBot) -> None:
        """
        Tests that nested tab content is laid out before the alpha snapshot.

        Args:
            qtbot (QtBot): Fixture for managing Qt widgets.
        """

        # given
        stacked_widget = StackedWidget()
        stacked_widget.resize(400, 300)
        stacked_widget.addWidget(QLabel("First page"))
        target_page = QWidget()
        target_layout = QVBoxLayout(target_page)
        nested_tabs = QTabWidget(target_page)
        nested_page = QLabel("Nested page")
        nested_tabs.addTab(nested_page, "Nested")
        target_layout.addWidget(nested_tabs)
        stacked_widget.addWidget(target_page)
        stacked_widget.setTransition(StackedWidget.Transition.Alpha)
        stacked_widget.setDuration(200)
        qtbot.addWidget(stacked_widget)
        stacked_widget.show()
        qtbot.waitUntil(stacked_widget.isVisible)

        # when
        stacked_widget.slideInIndex(1)

        # then
        qtbot.waitUntil(lambda: nested_page.size().isValid())
        assert nested_page.width() > 0
        assert nested_page.height() > 0
