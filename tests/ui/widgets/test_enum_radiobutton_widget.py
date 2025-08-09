"""
Copyright (c) Cutleast
"""

from enum import Enum

import pytest
from PySide6.QtWidgets import QRadioButton
from pytestqt.qtbot import QtBot

from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.enum_radiobutton_widget import EnumRadiobuttonsWidget


class TestEnumRadiobuttonsWidget(BaseTest):
    """
    Tests `ui.widgets.enum_radiobutton_widget.EnumRadiobuttonsWidget`.
    """

    class _TestEnum(Enum):
        """Test enum."""

        Item1 = 1
        Item2 = 2
        Item3 = 3

    ENUM_ITEMS: tuple[str, type[dict[_TestEnum, QRadioButton]]] = (
        "enum_items",
        dict[_TestEnum, QRadioButton],
    )
    """Identifier for accessing the private enum_items field."""

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> EnumRadiobuttonsWidget[_TestEnum]:
        """
        Fixture to create and provide an EnumRadiobuttonsWidget instance for tests.
        """

        enum_radiobuttons_widget = EnumRadiobuttonsWidget(
            TestEnumRadiobuttonsWidget._TestEnum,
            TestEnumRadiobuttonsWidget._TestEnum.Item1,
        )
        qtbot.addWidget(enum_radiobuttons_widget)
        enum_radiobuttons_widget.show()

        return enum_radiobuttons_widget

    def test_initial_state(self, widget: EnumRadiobuttonsWidget[_TestEnum]) -> None:
        """
        Test the initial state of the widget.
        """

        # given
        enum_items: dict[TestEnumRadiobuttonsWidget._TestEnum, QRadioButton] = (
            Utils.get_private_field(widget, *TestEnumRadiobuttonsWidget.ENUM_ITEMS)
        )

        # then
        assert enum_items[TestEnumRadiobuttonsWidget._TestEnum.Item1].isChecked()
        assert not enum_items[TestEnumRadiobuttonsWidget._TestEnum.Item2].isChecked()
        assert not enum_items[TestEnumRadiobuttonsWidget._TestEnum.Item3].isChecked()
        assert widget.getCurrentValue() == TestEnumRadiobuttonsWidget._TestEnum.Item1

    def test_change_emits_changed_signal(
        self, widget: EnumRadiobuttonsWidget[_TestEnum], qtbot: QtBot
    ) -> None:
        """
        Tests that the `currentValueChanged` signal is emitted when the checked
        radiobutton changes.
        """

        # given
        enum_items: dict[TestEnumRadiobuttonsWidget._TestEnum, QRadioButton] = (
            Utils.get_private_field(widget, *TestEnumRadiobuttonsWidget.ENUM_ITEMS)
        )

        # when
        with qtbot.waitSignal(widget.currentValueChanged) as signal:
            widget.setCurrentValue(TestEnumRadiobuttonsWidget._TestEnum.Item2)

        # then
        assert signal.args == [TestEnumRadiobuttonsWidget._TestEnum.Item2]
        assert widget.getCurrentValue() == TestEnumRadiobuttonsWidget._TestEnum.Item2

        # when
        with qtbot.waitSignal(widget.currentValueChanged) as signal:
            enum_items[TestEnumRadiobuttonsWidget._TestEnum.Item3].setChecked(True)

        # then
        assert signal.args == [TestEnumRadiobuttonsWidget._TestEnum.Item3]
        assert widget.getCurrentValue() == TestEnumRadiobuttonsWidget._TestEnum.Item3
