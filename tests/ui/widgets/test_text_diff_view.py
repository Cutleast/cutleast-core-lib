"""
Copyright (c) Cutleast
"""

from PySide6.QtWidgets import QPlainTextEdit
from pytestqt.qtbot import QtBot

from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.text_diff_view import TextDiffView


class TestTextDiffView(BaseTest):
    """
    Tests `cutleast_core_lib.ui.widgets.text_diff_view.TextDiffView`.
    """

    def test_set_texts_replaces_previous_diff(self, qtbot: QtBot) -> None:
        """
        Tests that displaying another diff replaces the previously displayed texts.
        """

        # given
        view = TextDiffView()
        qtbot.addWidget(view)
        view.set_texts("First", "Second")

        # when
        view.set_texts("Third", "Fourth")

        # then
        old_edit, new_edit = TestTextDiffView.__get_edits(view)
        assert old_edit.toPlainText() == "Third"
        assert new_edit.toPlainText() == "Fourth"

    @staticmethod
    def __get_edits(view: TextDiffView) -> tuple[QPlainTextEdit, QPlainTextEdit]:
        """
        Gets the text edits of a diff view.

        Args:
            view (TextDiffView): The diff view.

        Returns:
            tuple[QPlainTextEdit, QPlainTextEdit]: The edits of the old and new text.
        """

        return (
            Utils.get_private_field(view, "old_edit", QPlainTextEdit),
            Utils.get_private_field(view, "new_edit", QPlainTextEdit),
        )
