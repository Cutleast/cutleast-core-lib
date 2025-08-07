"""
Copyright (c) Cutleast
"""

import pytest
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from test.base_test import BaseTest
from test.utils import Utils
from ui.widgets.key_edit import KeyLineEdit


class TestKeyLineEdit(BaseTest):
    """
    Tests `ui.widgets.key_edit.KeyLineEdit`.
    """

    VISIBILITY_BUTTON: tuple[str, type[QPushButton]] = "visibility_button", QPushButton
    """Identifier for accessing the private visibility_button field."""

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> KeyLineEdit:
        """
        Fixture to create and provide a KeyLineEdit instance for tests.
        """

        key_line_edit = KeyLineEdit()
        qtbot.addWidget(key_line_edit)
        key_line_edit.show()

        return key_line_edit

    def test_initial_state(self, widget: KeyLineEdit) -> None:
        """
        Test the initial state of the widget.
        """

        # given
        visibility_button: QPushButton = Utils.get_private_field(
            widget, *TestKeyLineEdit.VISIBILITY_BUTTON
        )

        # then
        assert widget.text() == ""
        assert widget.echoMode() == KeyLineEdit.EchoMode.Password
        assert not visibility_button.isVisible()
        assert visibility_button.isEnabled()
        assert not visibility_button.isChecked()

    def test_toggle_visibility(self, widget: KeyLineEdit) -> None:
        """
        Tests that toggling the visibility button toggles the echo mode and changes the
        icon.
        """

        # given
        visibility_button: QPushButton = Utils.get_private_field(
            widget, *TestKeyLineEdit.VISIBILITY_BUTTON
        )
        old_icon: QIcon = visibility_button.icon()

        # when
        visibility_button.click()

        # then
        assert widget.echoMode() == KeyLineEdit.EchoMode.Normal
        assert visibility_button.isChecked()
        assert visibility_button.icon() != old_icon

        # when
        old_icon = visibility_button.icon()
        visibility_button.click()

        # then
        assert widget.echoMode() == KeyLineEdit.EchoMode.Password
        assert not visibility_button.isChecked()
        assert visibility_button.icon() != old_icon

    def test_text_makes_button_visible(self, widget: KeyLineEdit) -> None:
        """
        Tests that the visibility button is only visible when the text is not empty.
        """

        # given
        visibility_button: QPushButton = Utils.get_private_field(
            widget, *TestKeyLineEdit.VISIBILITY_BUTTON
        )

        # then
        assert not visibility_button.isVisible()

        # when
        widget.setText("some text")

        # then
        assert visibility_button.isVisible()

        # when
        widget.setText("")

        # then
        assert not visibility_button.isVisible()
