"""
Copyright (c) Cutleast
"""

from enum import Enum

import pytest
from pytestqt.qtbot import QtBot

from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.ui.widgets.enum_placeholder_dropdown import (
    EnumPlaceholderDropdown,
)


class TestEnumPlaceholderDropdown(BaseTest):
    """
    Tests `ui.widgets.enum_placeholder_dropdown.EnumPlaceholderDropdown`.
    """

    class _TestEnum(Enum):
        """Test enum."""

        Item1 = 1
        Item2 = 2
        Item3 = 3

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> EnumPlaceholderDropdown[_TestEnum]:
        """
        Fixture to create and provide an EnumPlaceholderDropdown instance for tests.
        """

        enum_dropdown = EnumPlaceholderDropdown(TestEnumPlaceholderDropdown._TestEnum)
        qtbot.addWidget(enum_dropdown)
        enum_dropdown.show()

        return enum_dropdown

    def test_initial_state(self, widget: EnumPlaceholderDropdown[_TestEnum]) -> None:
        """
        Test the initial state of the widget.
        """

        # then
        assert widget.currentIndex() == -1
        assert widget.itemText(0) == "Item1"
        assert widget.getCurrentValue() is None

    def test_change_emits_changed_signal(
        self, widget: EnumPlaceholderDropdown[_TestEnum], qtbot: QtBot
    ) -> None:
        """
        Tests that the `currentValueChanged` signal is emitted when the dropdown value
        is changed.
        """

        # when
        with qtbot.waitSignal(widget.currentValueChanged) as signal:
            widget.setCurrentValue(TestEnumPlaceholderDropdown._TestEnum.Item2)

        # then
        assert signal.args == [TestEnumPlaceholderDropdown._TestEnum.Item2]
        assert widget.getCurrentValue() == TestEnumPlaceholderDropdown._TestEnum.Item2

        # when
        with qtbot.waitSignal(widget.currentValueChanged) as signal:
            widget.setCurrentIndex(2)

        # then
        assert signal.args == [TestEnumPlaceholderDropdown._TestEnum.Item3]
        assert widget.getCurrentValue() == TestEnumPlaceholderDropdown._TestEnum.Item3
