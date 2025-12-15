"""
Copyright (c) Cutleast
"""

import pytest
from pytestqt.qtbot import QtBot

from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.placeholder_dropdown import PlaceholderDropdown


class TestPlaceholderDropdown(BaseTest):
    """
    Tests `ui.widgets.placeholder_dropdown.PlaceholderDropdown`.
    """

    PLACEHOLDER_TEXT: tuple[str, type[str]] = "placeholder_text", str
    """Identifier for accessing the private placeholder text field."""

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> PlaceholderDropdown:
        """
        Fixture to create and provide an PlaceholderDropdown instance for tests.
        """

        enum_dropdown = PlaceholderDropdown("PLACEHOLDER")
        qtbot.addWidget(enum_dropdown)
        enum_dropdown.show()

        return enum_dropdown

    def test_initial_state(self, widget: PlaceholderDropdown) -> None:
        """
        Test the initial state of the widget.
        """

        # given
        placeholder_text: str = Utils.get_private_field(
            widget, *TestPlaceholderDropdown.PLACEHOLDER_TEXT
        )

        assert widget.currentIndex() == -1
        assert widget.itemText(-1) == placeholder_text
        assert widget.currentText() == ""

    def test_placeholder_is_ignored(
        self, qtbot: QtBot, widget: PlaceholderDropdown
    ) -> None:
        """
        Tests that the placeholder item is ignored in `currentIndex` and `currentText`.
        """

        # given
        widget.addItems([f"Item {i}" for i in range(3)])

        # then
        assert widget.itemText(0) == "Item 0"
        assert widget.itemText(1) == "Item 1"
        assert widget.itemText(2) == "Item 2"
        assert widget.count() == 3

        # when
        with qtbot.waitSignal(widget.currentIndexChanged) as signal:
            widget.setCurrentIndex(1)

        # then
        assert signal.args == [2]  # signal emits the real index
        assert widget.currentIndex() == 1
        assert widget.currentText() == "Item 1"

        # when
        with qtbot.waitSignal(widget.currentIndexChanged) as signal:
            widget.setCurrentText("")

        # then
        assert signal.args == [0]  # signal emits the real index
        assert widget.currentIndex() == -1
        assert widget.currentText() == ""

        # when
        with qtbot.waitSignal(widget.currentIndexChanged) as signal:
            widget.setCurrentText("Item 2")

        # then
        assert signal.args == [3]  # signal emits the real index
        assert widget.currentIndex() == 2
        assert widget.currentText() == "Item 2"
