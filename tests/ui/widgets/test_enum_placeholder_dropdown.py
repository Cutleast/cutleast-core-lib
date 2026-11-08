"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Optional, override

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QComboBox
from pytestqt.qtbot import QtBot

from cutleast_core_lib.core.utilities.colored_enum import ColoredEnum
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

    class _ColoredTestEnum(ColoredEnum):
        """Colored test enum."""

        Red = 1
        Plain = 2

        @override
        def get_base_color(self) -> Optional[QColor]:
            return None

        @override
        def get_bg_color(self) -> Optional[QColor]:
            return None

        @override
        def get_highlighted_bg_color(self) -> Optional[QColor]:
            return None

        @override
        def get_fg_color(self) -> Optional[QColor]:
            if self.name == "Red":
                return QColor(255, 0, 0)

            return None

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

    def test_colored_enum_item_colors(self, qtbot: QtBot) -> None:
        """
        Tests that the foreground colors of a colored enum are applied to the items and
        to the closed dropdown, while the placeholder stays uncolored.
        """

        # given
        widget = EnumPlaceholderDropdown(TestEnumPlaceholderDropdown._ColoredTestEnum)
        qtbot.addWidget(widget)

        # then
        assert (
            QComboBox.itemData(widget, 0, Qt.ItemDataRole.ForegroundRole) is None
        )  # placeholder
        assert QComboBox.itemData(widget, 1, Qt.ItemDataRole.ForegroundRole) == QColor(
            255, 0, 0
        )
        assert QComboBox.itemData(widget, 2, Qt.ItemDataRole.ForegroundRole) is None
        assert widget.styleSheet() == ""

        # when
        widget.setCurrentValue(TestEnumPlaceholderDropdown._ColoredTestEnum.Red)

        # then
        assert (
            widget.styleSheet() == "QComboBox:enabled { color: rgba(255, 0, 0, 255); }"
        )

        # when
        widget.setCurrentValue(None)

        # then
        assert widget.styleSheet() == ""
