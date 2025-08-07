"""
Copyright (c) Cutleast
"""

from enum import Enum

import pytest
from PySide6.QtWidgets import QComboBox
from pytestqt.qtbot import QtBot

from test.base_test import BaseTest
from test.utils import Utils
from ui.widgets.enum_dropdown import EnumDropdown


class TestEnumDropdown(BaseTest):
    """
    Tests `ui.widgets.enum_dropdown.EnumDropdown`.
    """

    DROPDOWN: tuple[str, type[QComboBox]] = "dropdown", QComboBox
    """Identifier for accessing the private dropdown field."""

    class _TestEnum(Enum):
        """Test enum."""

        Item1 = 1
        Item2 = 2
        Item3 = 3

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> EnumDropdown[_TestEnum]:
        """
        Fixture to create and provide an EnumDropdown instance for tests.
        """

        enum_dropdown = EnumDropdown(
            TestEnumDropdown._TestEnum, TestEnumDropdown._TestEnum.Item1
        )
        qtbot.addWidget(enum_dropdown)
        enum_dropdown.show()

        return enum_dropdown

    def test_initial_state(self, widget: EnumDropdown[_TestEnum]) -> None:
        """
        Test the initial state of the widget.
        """

        # given
        dropdown: QComboBox = Utils.get_private_field(
            widget, *TestEnumDropdown.DROPDOWN
        )

        # then
        assert dropdown.currentIndex() == 0
        assert dropdown.itemText(0) == "Item1"
        assert widget.getCurrentValue() == TestEnumDropdown._TestEnum.Item1

    def test_change_emits_changed_signal(
        self, widget: EnumDropdown[_TestEnum], qtbot: QtBot
    ) -> None:
        """
        Tests that the `currentValueChanged` signal is emitted when the dropdown value
        is changed.
        """

        # given
        dropdown: QComboBox = Utils.get_private_field(
            widget, *TestEnumDropdown.DROPDOWN
        )

        # when
        with qtbot.waitSignal(widget.currentValueChanged) as signal:
            widget.setCurrentValue(TestEnumDropdown._TestEnum.Item2)

        # then
        assert signal.args == [TestEnumDropdown._TestEnum.Item2]
        assert widget.getCurrentValue() == TestEnumDropdown._TestEnum.Item2

        # when
        with qtbot.waitSignal(widget.currentValueChanged) as signal:
            dropdown.setCurrentIndex(2)

        # then
        assert signal.args == [TestEnumDropdown._TestEnum.Item3]
        assert widget.getCurrentValue() == TestEnumDropdown._TestEnum.Item3
