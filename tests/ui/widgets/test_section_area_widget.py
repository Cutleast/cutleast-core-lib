"""
Copyright (c) Cutleast
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QPushButton, QWidget
from pytestqt.qtbot import QtBot

from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.section_area_widget import SectionAreaWidget


class TestSectionAreaWidget(BaseTest):
    """
    Tests `ui.widgets.section_area_widget.SectionAreaWidget`.
    """

    HEADER_WIDGET: tuple[str, type[QWidget]] = "header_widget", QWidget
    """Identifier for accessing the private header_widget field."""

    CONTENT_WIDGET: tuple[str, type[QWidget]] = "content_widget", QWidget
    """Identifier for accessing the private content_widget field."""

    TOGGLE_BUTTON: tuple[str, type[QPushButton]] = "toggle_button", QPushButton
    """Identifier for accessing the private toggle_button field."""

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> SectionAreaWidget:
        """
        Fixture to create and provide a SectionAreaWidget instance for tests.
        """

        section_area_widget = SectionAreaWidget(
            header=QLabel("Header"), content=QPushButton("Content")
        )
        qtbot.addWidget(section_area_widget)
        section_area_widget.show()

        return section_area_widget

    def test_initial_state(self, widget: SectionAreaWidget) -> None:
        """
        Test the initial state of the widget.
        """

        # given
        header_widget: QWidget = Utils.get_private_field(
            widget, *TestSectionAreaWidget.HEADER_WIDGET
        )
        content_widget: QWidget = Utils.get_private_field(
            widget, *TestSectionAreaWidget.CONTENT_WIDGET
        )
        toggle_button: QPushButton = Utils.get_private_field(
            widget, *TestSectionAreaWidget.TOGGLE_BUTTON
        )

        # then
        assert header_widget.isVisible()
        assert not content_widget.isVisible()
        assert toggle_button.isVisible()
        assert not toggle_button.isChecked()

    def test_toggle(self, widget: SectionAreaWidget, qtbot: QtBot) -> None:
        """
        Test the toggle functionality of the widget.
        """

        # given
        content_widget: QWidget = Utils.get_private_field(
            widget, *TestSectionAreaWidget.CONTENT_WIDGET
        )
        toggle_button: QPushButton = Utils.get_private_field(
            widget, *TestSectionAreaWidget.TOGGLE_BUTTON
        )
        old_icon: QIcon = toggle_button.icon()

        # when
        with qtbot.waitSignal(widget.toggled) as signal:
            qtbot.mouseClick(toggle_button, Qt.MouseButton.LeftButton)

        # then
        assert signal.args == [True]
        assert content_widget.isVisible()
        assert widget.isExpanded()
        assert toggle_button.isChecked()
        assert toggle_button.icon() != old_icon

        # when
        old_icon = toggle_button.icon()
        with qtbot.waitSignal(widget.toggled) as signal:
            qtbot.mouseClick(toggle_button, Qt.MouseButton.LeftButton)

        # then
        assert signal.args == [False]
        assert not content_widget.isVisible()
        assert not widget.isExpanded()
        assert not toggle_button.isChecked()
        assert toggle_button.icon() != old_icon
