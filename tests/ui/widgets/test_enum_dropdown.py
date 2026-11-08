"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Optional, override

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QComboBox
from pytest_mock import MockerFixture
from pytestqt.qtbot import QtBot

from cutleast_core_lib.core.utilities.colored_enum import ColoredEnum
from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.widgets.enum_dropdown import EnumDropdown


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
        dropdown: QComboBox = Utils.get_private_field(widget, *TestEnumDropdown.DROPDOWN)

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
        dropdown: QComboBox = Utils.get_private_field(widget, *TestEnumDropdown.DROPDOWN)

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

    def test_colored_enum_item_colors(self, qtbot: QtBot) -> None:
        """
        Tests that the foreground colors of a colored enum are applied to the items and
        to the closed dropdown.
        """

        # given
        widget = EnumDropdown(
            TestEnumDropdown._ColoredTestEnum, TestEnumDropdown._ColoredTestEnum.Red
        )
        qtbot.addWidget(widget)
        dropdown: QComboBox = Utils.get_private_field(widget, *TestEnumDropdown.DROPDOWN)

        # then
        assert dropdown.itemData(0, Qt.ItemDataRole.ForegroundRole) == QColor(255, 0, 0)
        assert dropdown.itemData(1, Qt.ItemDataRole.ForegroundRole) is None
        assert (
            dropdown.styleSheet() == "QComboBox:enabled { color: rgba(255, 0, 0, 255); }"
        )

        # when
        widget.setCurrentValue(TestEnumDropdown._ColoredTestEnum.Plain)

        # then
        assert dropdown.styleSheet() == ""

    def test_uncolored_enum_has_no_item_colors(
        self, widget: EnumDropdown[_TestEnum]
    ) -> None:
        """
        Tests that items of an uncolored enum have no foreground color.
        """

        # given
        dropdown: QComboBox = Utils.get_private_field(widget, *TestEnumDropdown.DROPDOWN)

        # then
        assert dropdown.itemData(0, Qt.ItemDataRole.ForegroundRole) is None
        assert dropdown.styleSheet() == ""

    def test_theme_change_reapplies_colors(
        self, qtbot: QtBot, mocker: MockerFixture
    ) -> None:
        """
        Tests that the item colors are reapplied when the theme changes.
        """

        # given
        widget = EnumDropdown(
            TestEnumDropdown._ColoredTestEnum, TestEnumDropdown._ColoredTestEnum.Plain
        )
        qtbot.addWidget(widget)
        dropdown: QComboBox = Utils.get_private_field(widget, *TestEnumDropdown.DROPDOWN)
        mocker.patch.object(
            TestEnumDropdown._ColoredTestEnum,
            "get_fg_color",
            return_value=QColor(0, 0, 255),
        )
        theme_manager: ThemeManager = ThemeManager.get()

        # when
        theme_manager.theme_changed.emit(theme_manager.theme)

        # then
        assert dropdown.itemData(1, Qt.ItemDataRole.ForegroundRole) == QColor(0, 0, 255)
        assert (
            dropdown.styleSheet() == "QComboBox:enabled { color: rgba(0, 0, 255, 255); }"
        )
