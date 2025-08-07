"""
Copyright (c) Cutleast
"""

import pytest
from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from test.base_test import BaseTest
from test.utils import Utils
from ui.widgets.color_edit import ColorLineEdit


class TestColorLineEdit(BaseTest):
    """
    Tests `ui.widgets.color_edit.ColorLineEdit`.
    """

    PRESET_COLORS: tuple[str, type[list[str]]] = ("preset_colors", list[str])
    """Identifier for accessing the private preset_colors field."""

    CHOOSE_COLOR_BUTTON: tuple[str, type[QPushButton]] = (
        "choose_color_button",
        QPushButton,
    )
    """Identifier for accessing the private choose_color_button field."""

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> ColorLineEdit:
        """
        Fixture to create and provide a ColorLineEdit instance for tests.
        """

        color_edit = ColorLineEdit([])
        qtbot.addWidget(color_edit)
        color_edit.show()

        return color_edit

    def test_initial_state(self, widget: ColorLineEdit) -> None:
        """
        Test the initial state of the widget.
        """

        # given
        choose_color_button: QPushButton = Utils.get_private_field(
            widget, *TestColorLineEdit.CHOOSE_COLOR_BUTTON
        )

        # then
        assert widget.text() == ""
        assert choose_color_button.isVisible()
        assert choose_color_button.isEnabled()
