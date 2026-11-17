"""
Copyright (c) Cutleast
"""

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit


def replace_text(text_edit: QPlainTextEdit | QTextEdit, text: str) -> None:
    """
    Replaces the entire plain text of a text edit as a single undoable step. In contrast
    to `setPlainText()`, this keeps the undo history of the text edit.

    Args:
        text_edit (QPlainTextEdit | QTextEdit): The text edit whose text to replace.
        text (str): The new plain text.
    """

    cursor = QTextCursor(text_edit.document())
    cursor.beginEditBlock()
    cursor.select(QTextCursor.SelectionType.Document)
    cursor.insertText(text)
    cursor.endEditBlock()
