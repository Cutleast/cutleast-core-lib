"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QSplitter, QVBoxLayout, QWidget

from cutleast_core_lib.core.utilities.text_diff import DiffChunk, get_word_diff

from ..theme.manager import ThemeManager
from ..theme.models.theme import Theme
from .line_number_text_edit import LineNumberTextEdit


class TextDiffView(QWidget):
    """
    Displays two texts side by side with colored highlighting like common diff views:
    removed parts in red in the old text, added parts in green in the new text and
    changed parts (a removed part directly followed by an added part) in blue in both
    texts.
    """

    __old_title_label: QLabel
    __new_title_label: QLabel
    __old_edit: QPlainTextEdit
    __new_edit: QPlainTextEdit

    __old_text: str
    __new_text: str

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__old_text = ""
        self.__new_text = ""

        self.__init_ui()

        ThemeManager.get().theme_changed.connect(self.__on_theme_changed)

    def __init_ui(self) -> None:
        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vlayout)

        splitter = QSplitter()
        vlayout.addWidget(splitter)

        self.__old_title_label, self.__old_edit = self.__create_text_view(
            splitter, self.tr("Before")
        )
        self.__new_title_label, self.__new_edit = self.__create_text_view(
            splitter, self.tr("After")
        )

    def __create_text_view(
        self, splitter: QSplitter, title: str
    ) -> tuple[QLabel, QPlainTextEdit]:
        widget = QWidget()
        splitter.addWidget(widget)

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(vlayout)

        title_label = QLabel(title)
        title_label.setProperty("emphasized", True)
        vlayout.addWidget(title_label)

        text_edit = LineNumberTextEdit()
        text_edit.setReadOnly(True)
        vlayout.addWidget(text_edit, stretch=1)

        return title_label, text_edit

    def set_titles(self, old_title: str, new_title: str) -> None:
        """
        Sets the titles displayed above both texts.

        Args:
            old_title (str): The title of the old text.
            new_title (str): The title of the new text.
        """

        self.__old_title_label.setText(old_title)
        self.__new_title_label.setText(new_title)

    def set_texts(self, old_text: str, new_text: str) -> None:
        """
        Displays the differences between two texts.

        Args:
            old_text (str): The old text.
            new_text (str): The new text.
        """

        self.__old_text = old_text
        self.__new_text = new_text
        self.__render_diff()

    def __on_theme_changed(self, theme: Theme) -> None:
        self.__render_diff()

    def __render_diff(self) -> None:
        theme: Theme = ThemeManager.get().theme
        removed_format: QTextCharFormat = TextDiffView.__create_highlight_format(
            theme.resolve(theme.colors.error_bg),
            theme.resolve(theme.colors.error_fg),
        )
        added_format: QTextCharFormat = TextDiffView.__create_highlight_format(
            theme.resolve(theme.colors.success_bg),
            theme.resolve(theme.colors.success_fg),
        )
        changed_format: QTextCharFormat = TextDiffView.__create_highlight_format(
            theme.resolve(theme.colors.information_bg),
            theme.resolve(theme.colors.information_fg),
        )

        self.__old_edit.clear()
        self.__new_edit.clear()

        chunks: list[DiffChunk] = get_word_diff(self.__old_text, self.__new_text)
        old_cursor = QTextCursor(self.__old_edit.document())
        new_cursor = QTextCursor(self.__new_edit.document())
        for index, chunk in enumerate(chunks):
            previous_kind: Optional[DiffChunk.Kind] = (
                chunks[index - 1].kind if index > 0 else None
            )
            next_kind: Optional[DiffChunk.Kind] = (
                chunks[index + 1].kind if index + 1 < len(chunks) else None
            )

            match chunk.kind:
                case DiffChunk.Kind.Equal:
                    old_cursor.insertText(chunk.text, QTextCharFormat())
                    new_cursor.insertText(chunk.text, QTextCharFormat())
                case DiffChunk.Kind.Removed:
                    old_cursor.insertText(
                        chunk.text,
                        (
                            changed_format
                            if next_kind == DiffChunk.Kind.Added
                            else removed_format
                        ),
                    )
                case DiffChunk.Kind.Added:
                    new_cursor.insertText(
                        chunk.text,
                        (
                            changed_format
                            if previous_kind == DiffChunk.Kind.Removed
                            else added_format
                        ),
                    )

    @staticmethod
    def __create_highlight_format(bg_color: str, fg_color: str) -> QTextCharFormat:
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(bg_color))
        highlight_format.setForeground(QColor(fg_color))

        return highlight_format
