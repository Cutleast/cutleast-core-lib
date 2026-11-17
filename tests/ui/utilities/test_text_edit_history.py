"""
Copyright (c) Cutleast
"""

from PySide6.QtWidgets import QPlainTextEdit, QPushButton
from pytestqt.qtbot import QtBot

from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.utilities.text_edit_history import TextEditHistory


class TestTextEditHistory(BaseTest):
    """
    Tests `cutleast_core_lib.ui.utilities.text_edit_history.TextEditHistory`.
    """

    HISTORY_BUTTON: tuple[str, type[QPushButton]] = "history_button", QPushButton
    """Identifier for accessing the private history_button field."""

    @staticmethod
    def __create_history(
        qtbot: QtBot, idle_interval: int = 1000
    ) -> tuple[QPlainTextEdit, TextEditHistory]:
        """
        Creates a text edit with an initial text and a history for it.

        Args:
            qtbot (QtBot): The Qt bot fixture.
            idle_interval (int, optional): The idle interval. Defaults to 1000.

        Returns:
            tuple[QPlainTextEdit, TextEditHistory]: The text edit and its history.
        """

        text_edit = QPlainTextEdit("Initial")
        qtbot.addWidget(text_edit)

        return text_edit, TextEditHistory(text_edit, idle_interval)

    def test_records_revision_after_idle_interval(self, qtbot: QtBot) -> None:
        """
        Tests that a revision is recorded once the text stopped changing.
        """

        # given
        text_edit, history = TestTextEditHistory.__create_history(qtbot, 50)

        # when
        text_edit.setPlainText("Changed")
        text_edit.setPlainText("Changed again")

        # then
        assert [revision.text for revision in history.revisions] == ["Initial"]
        qtbot.waitUntil(lambda: len(history.revisions) == 2)
        assert history.revisions[-1].text == "Changed again"

    def test_commit_ignores_unchanged_text(self, qtbot: QtBot) -> None:
        """
        Tests that committing only records a revision if the text changed.
        """

        # given
        text_edit, history = TestTextEditHistory.__create_history(qtbot)

        # when
        history.commit()
        text_edit.setPlainText("Changed")
        history.commit()
        history.commit()

        # then
        assert [revision.text for revision in history.revisions] == [
            "Initial",
            "Changed",
        ]

    def test_clear(self, qtbot: QtBot) -> None:
        """
        Tests that clearing the history keeps only the current text as revision and
        discards pending changes.
        """

        # given
        text_edit, history = TestTextEditHistory.__create_history(qtbot, 50)
        text_edit.setPlainText("Changed")
        history.commit()
        text_edit.setPlainText("Other text")

        # when
        history.clear()
        qtbot.wait(100)

        # then
        assert [revision.text for revision in history.revisions] == ["Other text"]

    def test_restore_is_undoable(self, qtbot: QtBot) -> None:
        """
        Tests that restoring a revision records it as new revision and can be undone.
        """

        # given
        text_edit, history = TestTextEditHistory.__create_history(qtbot)
        text_edit.setPlainText("Changed")
        text_edit.textCursor().insertText("Typed ")

        # when
        history.restore(history.revisions[0])

        # then
        assert text_edit.toPlainText() == "Initial"
        assert [revision.text for revision in history.revisions] == [
            "Initial",
            "Typed Changed",
            "Initial",
        ]

        # when
        text_edit.undo()

        # then
        assert text_edit.toPlainText() == "Typed Changed"

    def test_button_enabled_with_multiple_revisions(self, qtbot: QtBot) -> None:
        """
        Tests that the history button is only enabled if there is something to restore.
        """

        # given
        text_edit, history = TestTextEditHistory.__create_history(qtbot)
        button: QPushButton = Utils.get_private_field(
            history, *TestTextEditHistory.HISTORY_BUTTON
        )

        # then
        assert not button.isEnabled()

        # when
        text_edit.setPlainText("Changed")
        history.commit()

        # then
        assert button.isEnabled()

        # when
        history.clear()

        # then
        assert not button.isEnabled()
