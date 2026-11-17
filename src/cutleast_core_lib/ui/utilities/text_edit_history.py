"""
Copyright (c) Cutleast
"""

from datetime import datetime
from typing import Optional, override

from pydantic import BaseModel
from PySide6.QtCore import QEvent, QObject, QRect, QTimer, Signal
from PySide6.QtWidgets import QPlainTextEdit, QPushButton, QTextEdit

from ..theme.manager import ThemeManager
from ..widgets.icon_button import IconButton
from ..widgets.text_history_dialog import TextHistoryDialog
from .icon_provider import IconProvider
from .text_edit import replace_text


class TextEditHistory(QObject):
    """
    Records the edit history of a text edit as revisions of its plain text, regardless of
    whether the text was changed by the user or programmatically. A revision is recorded
    once the text has not changed for a certain interval or when `commit()` is called.

    Optionally, a small button is placed in the top-right corner of the text edit, which
    opens a dialog for viewing the history and restoring revisions.
    """

    class Revision(BaseModel, frozen=True):
        """
        Represents a recorded state of the text of a text edit.
        """

        text: str
        """The plain text at the time of the revision."""

        timestamp: datetime
        """The point in time at which the revision was recorded."""

    revisions_changed = Signal()
    """Signal emitted when a revision was recorded or the history was cleared."""

    __text_edit: QPlainTextEdit | QTextEdit
    __revisions: list[Revision]
    __commit_timer: QTimer
    __history_button: Optional[QPushButton]

    def __init__(
        self,
        text_edit: QPlainTextEdit | QTextEdit,
        idle_interval: int = 1000,
        show_button: bool = True,
    ) -> None:
        """
        Args:
            text_edit (QPlainTextEdit | QTextEdit):
                The text edit whose history to record. It also becomes the parent of the
                history.
            idle_interval (int, optional):
                The time in milliseconds without changes after which a revision is
                recorded. Defaults to 1000.
            show_button (bool, optional):
                Whether to place a button for opening the history dialog in the text
                edit. Defaults to True.
        """

        super().__init__(text_edit)

        self.__text_edit = text_edit
        self.__revisions = [self.__create_revision()]

        self.__commit_timer = QTimer(self)
        self.__commit_timer.setSingleShot(True)
        self.__commit_timer.setInterval(idle_interval)

        self.__history_button = None
        if show_button:
            self.__init_button()

        self.__commit_timer.timeout.connect(self.commit)
        self.__text_edit.textChanged.connect(self.__commit_timer.start)
        if self.__history_button is not None:
            self.__history_button.clicked.connect(self.open_dialog)
            self.revisions_changed.connect(self.__update_button)

    def __init_button(self) -> None:
        self.__history_button = IconButton()
        self.__history_button.setParent(self.__text_edit)
        IconProvider.bind_qta_icon(
            self.__history_button, self.__history_button.setIcon, "mdi6.history"
        )
        self.__history_button.setToolTip(self.tr("Edit history"))
        self.__history_button.setFixedSize(39, 36)
        self.__history_button.show()
        self.__update_button()

        self.__text_edit.setProperty("has_button", True)
        ThemeManager.update_widget_styles(self.__text_edit)

        # The viewport is resized as well when scroll bars appear or disappear.
        self.__text_edit.installEventFilter(self)
        self.__text_edit.viewport().installEventFilter(self)

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self.__update_button_position()

        return super().eventFilter(watched, event)

    def __update_button_position(self) -> None:
        if self.__history_button is None:
            return

        edit_area: QRect = self.__text_edit.geometry()
        self.__history_button.move(
            edit_area.width() - self.__history_button.width(),
            0,
        )
        self.__history_button.raise_()

    def __update_button(self) -> None:
        if self.__history_button is not None:
            self.__history_button.setEnabled(len(self.__revisions) > 1)

    def __create_revision(self) -> Revision:
        return TextEditHistory.Revision(
            text=self.__text_edit.toPlainText(), timestamp=datetime.now()
        )

    @property
    def revisions(self) -> list[Revision]:
        """The recorded revisions, ordered from oldest to newest."""

        return list(self.__revisions)

    def commit(self) -> None:
        """
        Records the current text as a new revision immediately, if it differs from the
        latest revision.
        """

        self.__commit_timer.stop()

        revision: TextEditHistory.Revision = self.__create_revision()
        if revision.text == self.__revisions[-1].text:
            return

        self.__revisions.append(revision)
        self.revisions_changed.emit()

    def clear(self) -> None:
        """
        Discards all revisions and starts a new history with the current text as its
        only revision.
        """

        self.__commit_timer.stop()
        self.__revisions = [self.__create_revision()]
        self.revisions_changed.emit()

    def restore(self, revision: Revision) -> None:
        """
        Restores the text of a revision as an undoable change and records it as a new
        revision.

        Args:
            revision (Revision): The revision to restore.
        """

        self.commit()
        replace_text(self.__text_edit, revision.text)
        self.commit()

    def open_dialog(self) -> None:
        """
        Records pending changes and opens a dialog for viewing the history and restoring
        revisions.
        """

        self.commit()

        dialog = TextHistoryDialog(self, self.__text_edit)
        dialog.exec()
