"""
Copyright (c) Cutleast
"""

from collections.abc import Generator
from pathlib import Path

import pytest
from PySide6.QtWidgets import QCheckBox, QListWidget, QPlainTextEdit, QPushButton
from pytestqt.qtbot import QtBot

from cutleast_core_lib.core.utilities.typing_utils import not_none
from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.utilities.text_edit_history import TextEditHistory
from cutleast_core_lib.ui.widgets.text_diff_view import TextDiffView
from cutleast_core_lib.ui.widgets.text_history_dialog import TextHistoryDialog


class TestTextHistoryDialog(BaseTest):
    """
    Tests `cutleast_core_lib.ui.widgets.text_history_dialog.TextHistoryDialog`.
    """

    REVISIONS_LIST: tuple[str, type[QListWidget]] = "revisions_list", QListWidget
    """Identifier for accessing the private revisions_list field."""

    COMPARE_PREVIOUS_BOX: tuple[str, type[QCheckBox]] = (
        "compare_previous_box",
        QCheckBox,
    )
    """Identifier for accessing the private compare_previous_box field."""

    DIFF_VIEW: tuple[str, type[TextDiffView]] = "diff_view", TextDiffView
    """Identifier for accessing the private diff_view field."""

    RESTORE_BUTTON: tuple[str, type[QPushButton]] = "restore_button", QPushButton
    """Identifier for accessing the private restore_button field."""

    @pytest.fixture(autouse=True)
    def widget_state_manager(self, tmp_path: Path) -> Generator[WidgetStateManager]:
        """
        Provides a widget state manager, which is required by the dialog.

        Args:
            tmp_path (Path): The temporary folder of the test.

        Yields:
            WidgetStateManager: The widget state manager.
        """

        yield WidgetStateManager(tmp_path)

        Utils.reset_singleton(WidgetStateManager)

    @pytest.fixture
    def text_edit(self, qtbot: QtBot) -> QPlainTextEdit:
        """
        Creates a text edit with three revisions recorded in its history.

        Args:
            qtbot (QtBot): The Qt bot fixture.

        Returns:
            QPlainTextEdit: The text edit.
        """

        text_edit = QPlainTextEdit("First")
        qtbot.addWidget(text_edit)

        history = TextEditHistory(text_edit)
        text_edit.setPlainText("Second")
        history.commit()
        text_edit.setPlainText("Third")
        history.commit()

        return text_edit

    @staticmethod
    def __get_history(text_edit: QPlainTextEdit) -> TextEditHistory:
        """
        Gets the history of a text edit.

        Args:
            text_edit (QPlainTextEdit): The text edit.

        Returns:
            TextEditHistory: The history.
        """

        history: TextEditHistory = not_none(text_edit.findChild(TextEditHistory))

        return history

    @staticmethod
    def __get_diff_texts(dialog: TextHistoryDialog) -> tuple[str, str]:
        """
        Gets the texts currently displayed in the diff view of a dialog.

        Args:
            dialog (TextHistoryDialog): The dialog.

        Returns:
            tuple[str, str]: The old and the new text.
        """

        diff_view: TextDiffView = Utils.get_private_field(
            dialog, *TestTextHistoryDialog.DIFF_VIEW
        )

        return (
            Utils.get_private_field(diff_view, "old_edit", QPlainTextEdit).toPlainText(),
            Utils.get_private_field(diff_view, "new_edit", QPlainTextEdit).toPlainText(),
        )

    def test_lists_revisions_newest_first(
        self, qtbot: QtBot, text_edit: QPlainTextEdit
    ) -> None:
        """
        Tests that the revisions are listed newest first and that the revision before
        the current one is compared with the current text initially.
        """

        # when
        dialog = TextHistoryDialog(
            TestTextHistoryDialog.__get_history(text_edit), text_edit
        )
        qtbot.addWidget(dialog)

        # then
        revisions_list: QListWidget = Utils.get_private_field(
            dialog, *TestTextHistoryDialog.REVISIONS_LIST
        )
        labels: list[str] = [
            revisions_list.item(row).text() for row in range(revisions_list.count())
        ]
        assert len(labels) == 3
        assert "Third" in labels[0] and "(current)" in labels[0]
        assert "Second" in labels[1]
        assert "First" in labels[2]
        assert revisions_list.currentRow() == 1
        assert TestTextHistoryDialog.__get_diff_texts(dialog) == ("Second", "Third")

    def test_compare_with_previous_revision(
        self, qtbot: QtBot, text_edit: QPlainTextEdit
    ) -> None:
        """
        Tests that the selected revision can be compared with its predecessor.
        """

        # given
        dialog = TextHistoryDialog(
            TestTextHistoryDialog.__get_history(text_edit), text_edit
        )
        qtbot.addWidget(dialog)
        compare_previous_box: QCheckBox = Utils.get_private_field(
            dialog, *TestTextHistoryDialog.COMPARE_PREVIOUS_BOX
        )

        # when
        compare_previous_box.setChecked(True)

        # then
        assert TestTextHistoryDialog.__get_diff_texts(dialog) == ("First", "Second")

    def test_restore(self, qtbot: QtBot, text_edit: QPlainTextEdit) -> None:
        """
        Tests that the selected revision can be restored, but not the current one.
        """

        # given
        dialog = TextHistoryDialog(
            TestTextHistoryDialog.__get_history(text_edit), text_edit
        )
        qtbot.addWidget(dialog)
        revisions_list: QListWidget = Utils.get_private_field(
            dialog, *TestTextHistoryDialog.REVISIONS_LIST
        )
        restore_button: QPushButton = Utils.get_private_field(
            dialog, *TestTextHistoryDialog.RESTORE_BUTTON
        )

        # when
        revisions_list.setCurrentRow(0)

        # then
        assert not restore_button.isEnabled()

        # when
        revisions_list.setCurrentRow(2)
        restore_button.click()

        # then
        assert text_edit.toPlainText() == "First"
        assert dialog.result() == TextHistoryDialog.DialogCode.Accepted
