"""
Copyright (c) Cutleast
"""

from collections.abc import Callable

import pytest
from cutleast_core_lib.core.utilities.clipboard import Clipboard
from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.setup.clipboard_mock import ClipboardMock
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.tree_widget_editor import TreeWidgetEditor
from pydantic import BaseModel
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QShortcut
from PySide6.QtWidgets import QTreeWidgetItem
from pytestqt.qtbot import QtBot


class TestTreeWidgetEditor(BaseTest):
    """
    Tests `ui.widgets.tree_widget_editor.TreeWidgetEditor`.
    """

    class SampleObject(BaseModel):
        """A simple class to test the TreeWidgetEditor."""

        name: str
        value: str

    ITEMS: tuple[str, type[ReferenceDict[SampleObject, QTreeWidgetItem]]] = (
        "items",
        ReferenceDict,
    )
    """Identifier for accessing the protected items field."""

    REMOVE_ACTION: tuple[str, type[QAction]] = "remove_action", QAction
    """Identifier for accessing the protected remove_action field."""

    TREE_WIDGET: tuple[str, type[TreeWidgetEditor.TreeWidget]] = (
        "tree_widget",
        TreeWidgetEditor.TreeWidget,
    )
    """Identifier for accessing the protected tree_widget field."""

    @pytest.fixture
    def widget(self, qtbot: QtBot) -> TreeWidgetEditor[SampleObject]:
        """
        Fixture that creates and provides a TreeWidgetEditor instance for tests.
        """

        tree_widget_editor: TreeWidgetEditor[TestTreeWidgetEditor.SampleObject] = (
            TreeWidgetEditor(TestTreeWidgetEditor.SampleObject)
        )
        qtbot.addWidget(tree_widget_editor)
        return tree_widget_editor

    def test_initial_state(self, widget: TreeWidgetEditor[SampleObject]) -> None:
        """
        Test the initial state of the widget.
        """

        # given
        items: ReferenceDict[TestTreeWidgetEditor.SampleObject, QTreeWidgetItem] = (
            Utils.get_protected_field(widget, *TestTreeWidgetEditor.ITEMS)
        )
        remove_action: QAction = Utils.get_protected_field(
            widget, *TestTreeWidgetEditor.REMOVE_ACTION
        )
        tree_widget: TreeWidgetEditor.TreeWidget = Utils.get_protected_field(
            widget, *TestTreeWidgetEditor.TREE_WIDGET
        )

        # then
        assert len(items) == 0
        assert not remove_action.isEnabled()
        assert widget.getItems() == []
        assert tree_widget.topLevelItemCount() == 0

    def test_toggles_clipboard_actions(
        self, widget: TreeWidgetEditor[SampleObject]
    ) -> None:
        """Tests toggling the clipboard context menu and shortcuts."""

        # given
        tree_widget: TreeWidgetEditor.TreeWidget = Utils.get_protected_field(
            widget, *TestTreeWidgetEditor.TREE_WIDGET
        )
        shortcuts: list[QShortcut] = widget.findChildren(QShortcut)

        # when
        widget.setClipboardActionsEnabled(False)

        # then
        assert tree_widget.contextMenuPolicy() == Qt.ContextMenuPolicy.NoContextMenu
        assert shortcuts
        assert all(not shortcut.isEnabled() for shortcut in shortcuts)

        # when
        widget.setClipboardActionsEnabled(True)

        # then
        assert (
            tree_widget.contextMenuPolicy()
            == Qt.ContextMenuPolicy.CustomContextMenu
        )
        assert all(shortcut.isEnabled() for shortcut in shortcuts)

    def test_cut_item(
        self, widget: TreeWidgetEditor[SampleObject], clipboard: ClipboardMock
    ) -> None:
        """
        Tests cutting an item. This is like copying it and then removing it.
        """

        # given
        item: TestTreeWidgetEditor.SampleObject = TestTreeWidgetEditor.SampleObject(
            name="item", value="value"
        )
        widget.addItem(item)
        widget.setCurrentItem(item)
        cut_method: Callable[[], None] = Utils.get_private_method(
            widget, "cut_cur_item", lambda: None
        )

        # when
        cut_method()

        # then
        assert Clipboard.paste(TestTreeWidgetEditor.SampleObject) == item
        assert widget.getItems() == []

    def test_copy_item(
        self, widget: TreeWidgetEditor[SampleObject], clipboard: ClipboardMock
    ) -> None:
        """
        Tests copying a JSON representation of the current item.
        """

        # given
        item: TestTreeWidgetEditor.SampleObject = TestTreeWidgetEditor.SampleObject(
            name="item", value="value"
        )
        widget.addItem(item)
        widget.setCurrentItem(item)
        copy_method: Callable[[], None] = Utils.get_private_method(
            widget, "copy_cur_item", lambda: None
        )

        # when
        copy_method()

        # then
        assert Clipboard.paste(TestTreeWidgetEditor.SampleObject) == item

    def test_paste_item(
        self, widget: TreeWidgetEditor[SampleObject], clipboard: ClipboardMock
    ) -> None:
        """
        Tests pasting an item from the clipboard by deserializing it from JSON.
        """

        # given
        item: TestTreeWidgetEditor.SampleObject = TestTreeWidgetEditor.SampleObject(
            name="item", value="value"
        )
        paste_method: Callable[[], None] = Utils.get_private_method(
            widget, "paste_item", lambda: None
        )
        Clipboard.copy(item)

        # when
        paste_method()

        # then
        assert widget.getItems() == [item]

        # given
        clipboard.setText("")

        # when (test that it doesn't raise an error)
        paste_method()
