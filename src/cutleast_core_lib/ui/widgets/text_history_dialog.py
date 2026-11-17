"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from cutleast_core_lib.core.utilities.truncate import raw_string

from ..utilities.state_manager import WidgetStateManager
from .text_diff_view import TextDiffView

if TYPE_CHECKING:
    from ..utilities.text_edit_history import TextEditHistory


class TextHistoryDialog(QDialog):
    """
    Dialog for viewing the revisions recorded by a `TextEditHistory` and restoring one
    of them.
    """

    PREVIEW_LENGTH: int = 60
    """The maximum length of the text preview of a revision in the list."""

    __history: TextEditHistory
    __revisions: list[TextEditHistory.Revision]

    __revisions_list: QListWidget
    __compare_previous_box: QCheckBox
    __diff_view: TextDiffView
    __restore_button: QPushButton
    __close_button: QPushButton

    def __init__(self, history: TextEditHistory, parent: Optional[QWidget]) -> None:
        """
        Args:
            history (TextEditHistory): The history to display.
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__history = history
        self.__revisions = history.revisions

        self.__init_ui()

        self.__revisions_list.currentRowChanged.connect(lambda _: self.__update_diff())
        self.__compare_previous_box.toggled.connect(lambda _: self.__update_diff())
        self.__restore_button.clicked.connect(self.__restore)
        self.__close_button.clicked.connect(self.reject)

        # Preselect the revision before the current one, if there is any.
        self.__revisions_list.setCurrentRow(min(1, len(self.__revisions) - 1))
        self.__update_diff()

    def __init_ui(self) -> None:
        self.setWindowTitle(self.tr("Edit history"))
        self.resize(1100, 500)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        splitter = QSplitter()
        vlayout.addWidget(splitter, stretch=1)

        self.__revisions_list = QListWidget()
        splitter.addWidget(self.__revisions_list)
        self.__init_revisions_list()

        diff_widget = QWidget()
        splitter.addWidget(diff_widget)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([350, 750])

        diff_vlayout = QVBoxLayout()
        diff_vlayout.setContentsMargins(0, 0, 0, 0)
        diff_widget.setLayout(diff_vlayout)

        self.__diff_view = TextDiffView()
        diff_vlayout.addWidget(self.__diff_view, stretch=1)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.__compare_previous_box = QCheckBox(
            self.tr("Compare with previous revision")
        )
        hlayout.addWidget(self.__compare_previous_box)

        hlayout.addStretch()

        self.__restore_button = QPushButton(self.tr("Restore"))
        self.__restore_button.setProperty("primary", True)
        hlayout.addWidget(self.__restore_button)

        self.__close_button = QPushButton(self.tr("Close"))
        hlayout.addWidget(self.__close_button)

        WidgetStateManager.get().register_geometry("text_history_dialog", self)
        WidgetStateManager.get().register_state("text_history_dialog_splitter", splitter)
        WidgetStateManager.get().register_checkbox(
            "text_history_dialog_compare_previous", self.__compare_previous_box
        )

    def __init_revisions_list(self) -> None:
        last_index: int = len(self.__revisions) - 1
        for index in range(last_index, -1, -1):
            revision: TextEditHistory.Revision = self.__revisions[index]
            label: str = f"{revision.timestamp:%H:%M:%S}"
            if index == last_index:
                label += " " + self.tr("(current)")
            label += f" - {raw_string(revision.text, TextHistoryDialog.PREVIEW_LENGTH)}"

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setToolTip(revision.text)
            self.__revisions_list.addItem(item)

    def __get_selected_index(self) -> int:
        row: int = self.__revisions_list.currentRow()
        if row < 0:
            return len(self.__revisions) - 1

        item: QListWidgetItem = self.__revisions_list.item(row)

        return int(item.data(Qt.ItemDataRole.UserRole))

    def __update_diff(self) -> None:
        index: int = self.__get_selected_index()
        selected_text: str = self.__revisions[index].text

        if self.__compare_previous_box.isChecked():
            previous_text: str = self.__revisions[max(index - 1, 0)].text
            self.__diff_view.set_titles(
                self.tr("Previous revision"), self.tr("Selected revision")
            )
            self.__diff_view.set_texts(previous_text, selected_text)
        else:
            self.__diff_view.set_titles(
                self.tr("Selected revision"), self.tr("Current text")
            )
            self.__diff_view.set_texts(selected_text, self.__revisions[-1].text)

        self.__restore_button.setEnabled(index != len(self.__revisions) - 1)

    def __restore(self) -> None:
        self.__history.restore(self.__revisions[self.__get_selected_index()])
        self.accept()
