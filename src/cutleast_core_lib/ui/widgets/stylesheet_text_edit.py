"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Optional, override

from PySide6.QtCore import (
    QRegularExpression,
    QRegularExpressionMatch,
    QRegularExpressionMatchIterator,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeyEvent,
    QSyntaxHighlighter,
    QTextBlock,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
)
from PySide6.QtWidgets import QTextEdit, QWidget

from ..theme.manager import ThemeManager
from ..theme.models.theme import Theme
from .line_number_text_edit import LineNumberTextEdit


class QssSyntaxHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for Qt style sheets.
    """

    __COMMENT_STATE: int = 1
    __SELECTOR_PATTERN: str = r"^[^{}]+(?=\s*\{)"
    __IDENTIFIER_PATTERN: str = r"#[A-Za-z_][\w-]*"
    __PSEUDO_SELECTOR_PATTERN: str = r"::?[A-Za-z_][\w-]*"
    __PROPERTY_PATTERN: str = r"\b[A-Za-z-]+(?=\s*:)"
    __DOUBLE_QUOTED_STRING_PATTERN: str = r'"(?:\\.|[^"\\])*"'
    __SINGLE_QUOTED_STRING_PATTERN: str = r"'(?:\\.|[^'\\])*'"
    __COLOR_PATTERN: str = r"#[0-9A-Fa-f]{3,8}\b"
    __NUMBER_PATTERN: str = r"\b\d+(?:\.\d+)?(?:px|pt|em|ex|%)?\b"
    __KEYWORD_PATTERN: str = (
        r"\b(?:rgba?|hsla?|url|qlineargradient|qradialgradient|"
        r"qconicalgradient)\b"
    )

    __rules: list[tuple[QRegularExpression, QTextCharFormat]]
    __comment_format: QTextCharFormat

    @override
    def __init__(self, document: QTextDocument) -> None:
        """
        Args:
            document (QTextDocument): Document whose QSS content is highlighted.
        """

        super().__init__(document)

        self.update_theme(ThemeManager.get().theme)

    def update_theme(self, theme: Theme) -> None:
        """
        Updates the syntax colors for the specified theme.

        Args:
            theme (Theme): The theme that supplies semantic syntax colors.
        """

        self.__rules = self.__create_rules(theme)
        self.__comment_format = QssSyntaxHighlighter.__format(
            theme.resolve(theme.texts.secondary.color), italic=True
        )
        self.rehighlight()

    @staticmethod
    def __format(
        color: str, *, bold: bool = False, italic: bool = False
    ) -> QTextCharFormat:
        """
        Creates a text format for a syntax category.

        Args:
            color (str): Resolved color for the text format.
            bold (bool, optional): Whether the text should be bold. Defaults to False.
            italic (bool, optional): Whether the text should be italic. Defaults to False.

        Returns:
            QTextCharFormat: The configured text format.
        """

        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))
        text_format.setFontItalic(italic)

        if bold:
            text_format.setFontWeight(QFont.Weight.Bold)

        return text_format

    def __create_rules(
        self, theme: Theme
    ) -> list[tuple[QRegularExpression, QTextCharFormat]]:
        """
        Creates syntax highlighting rules for the specified theme.

        Args:
            theme (Theme): The theme that supplies semantic syntax colors.

        Returns:
            list[tuple[QRegularExpression, QTextCharFormat]]: Highlighting rules.
        """

        selector = QssSyntaxHighlighter.__format(
            theme.resolve(theme.colors.primary_fg), bold=True
        )
        identifier = QssSyntaxHighlighter.__format(
            theme.resolve(theme.colors.caution_fg)
        )
        property_name = QssSyntaxHighlighter.__format(
            theme.resolve(theme.colors.information_fg)
        )
        string: QTextCharFormat = QssSyntaxHighlighter.__format(
            theme.resolve(theme.colors.success_fg)
        )
        number: QTextCharFormat = QssSyntaxHighlighter.__format(
            theme.resolve(theme.colors.warning_fg)
        )
        color: QTextCharFormat = QssSyntaxHighlighter.__format(
            theme.resolve(theme.colors.warning_fg)
        )
        keyword: QTextCharFormat = QssSyntaxHighlighter.__format(
            theme.resolve(theme.colors.primary_fg)
        )

        return [
            (QRegularExpression(QssSyntaxHighlighter.__SELECTOR_PATTERN), selector),
            (QRegularExpression(QssSyntaxHighlighter.__IDENTIFIER_PATTERN), identifier),
            (
                QRegularExpression(QssSyntaxHighlighter.__PSEUDO_SELECTOR_PATTERN),
                keyword,
            ),
            (QRegularExpression(QssSyntaxHighlighter.__PROPERTY_PATTERN), property_name),
            (
                QRegularExpression(QssSyntaxHighlighter.__DOUBLE_QUOTED_STRING_PATTERN),
                string,
            ),
            (
                QRegularExpression(QssSyntaxHighlighter.__SINGLE_QUOTED_STRING_PATTERN),
                string,
            ),
            (QRegularExpression(QssSyntaxHighlighter.__COLOR_PATTERN), color),
            (QRegularExpression(QssSyntaxHighlighter.__NUMBER_PATTERN), number),
            (QRegularExpression(QssSyntaxHighlighter.__KEYWORD_PATTERN), keyword),
        ]

    @override
    def highlightBlock(self, text: str) -> None:
        for pattern, text_format in self.__rules:
            match_iterator: QRegularExpressionMatchIterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match: QRegularExpressionMatch = match_iterator.next()
                self.setFormat(
                    match.capturedStart(), match.capturedLength(), text_format
                )

        self.setCurrentBlockState(0)
        start: int = 0
        if self.previousBlockState() != QssSyntaxHighlighter.__COMMENT_STATE:
            start = text.find("/*")

        while start >= 0:
            end: int = text.find("*/", start + 2)
            length: int
            if end < 0:
                self.setCurrentBlockState(QssSyntaxHighlighter.__COMMENT_STATE)
                length = len(text) - start
            else:
                length = end - start + 2

            self.setFormat(start, length, self.__comment_format)
            start = text.find("/*", start + length)


class StylesheetTextEdit(LineNumberTextEdit):
    """
    QSS editor with common code-editing conveniences.
    """

    searchRequested = Signal()
    """Signal emitted when the editor's search UI should be shown."""

    cursorPositionInfoChanged = Signal(int, int)
    """
    Signal emitted when the cursor position changes.

    Args:
        int: One-based line number.
        int: One-based column number.
    """

    __OPENING_PAIRS: dict[str, str] = {
        "{": "}",
        "(": ")",
        "[": "]",
        '"': '"',
        "'": "'",
    }
    __CLOSING_CHARS: frozenset[str] = frozenset(__OPENING_PAIRS.values())
    __BRACKET_PAIRS: dict[str, str] = {
        "{": "}",
        "(": ")",
        "[": "]",
    }
    __indent_size: int
    __use_tabs: bool

    __highlighter: QssSyntaxHighlighter

    @override
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        indent_size: int = 4,
        use_tabs: bool = False,
    ) -> None:
        """
        Args:
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
            indent_size (int, optional): Spaces in one indent level. Defaults to 4.
            use_tabs (bool, optional): Whether indentation uses tabs. Defaults to False.
        """

        super().__init__(parent)

        self.__indent_size = max(1, indent_size)
        self.__use_tabs = use_tabs
        self.__highlighter = QssSyntaxHighlighter(self.document())

        self.setProperty("monospace", True)
        self.setFont(ThemeManager.get().theme.texts.monospace.as_qfont())

        self.__update_extra_selections()

        self.cursorPositionChanged.connect(self.__update_extra_selections)
        self.cursorPositionChanged.connect(self.__emit_cursor_position)
        ThemeManager.get().theme_changed.connect(self.__on_theme_changed)

    @property
    def indent_text(self) -> str:
        """Text inserted for one indentation level."""

        return "\t" if self.__use_tabs else " " * self.__indent_size

    def find_text(
        self, text: str, *, backwards: bool = False, case_sensitive: bool = False
    ) -> bool:
        """
        Finds text from the cursor, wrapping once at the document boundary.

        Args:
            text (str): Text to find.
            backwards (bool, optional): Whether to search backwards. Defaults to False.
            case_sensitive (bool, optional): Whether matching respects case.
                Defaults to False.

        Returns:
            bool: Whether a matching occurrence was found.
        """

        if not text:
            return False

        flags = QTextDocument.FindFlag(0)
        if backwards:
            flags |= QTextDocument.FindFlag.FindBackward

        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if self.find(text, flags):
            return True

        cursor: QTextCursor = self.textCursor()
        cursor.movePosition(
            QTextCursor.MoveOperation.End
            if backwards
            else QTextCursor.MoveOperation.Start
        )
        self.setTextCursor(cursor)
        return self.find(text, flags)

    def __toggle_comment(self) -> None:
        """
        Toggles QSS block comments around the selection or current line.
        """

        cursor: QTextCursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)

        selected: str = cursor.selectedText().replace("\u2029", "\n")
        stripped: str = selected.strip()
        replacement: str
        if stripped.startswith("/*") and stripped.endswith("*/"):
            start: int = selected.find("/*")
            end: int = selected.rfind("*/")
            replacement = (
                selected[:start] + selected[start + 2 : end] + selected[end + 2 :]
            )
        else:
            replacement = f"/*{selected}*/"

        cursor.insertText(replacement)
        self.setTextCursor(cursor)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        modifiers: Qt.KeyboardModifier = event.modifiers()
        ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)

        if ctrl and event.key() == Qt.Key.Key_F:
            self.searchRequested.emit()
            return

        if ctrl and (
            event.key() in (Qt.Key.Key_Slash, Qt.Key.Key_NumberSign)
            or event.text() == "#"
        ):
            self.__toggle_comment()
            return

        if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            self.__change_indentation(event.key() == Qt.Key.Key_Backtab)
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.__insert_newline()
            return

        text: str = event.text()
        if text in StylesheetTextEdit.__OPENING_PAIRS:
            self.__insert_pair(text, StylesheetTextEdit.__OPENING_PAIRS[text])
            return

        if (
            text in StylesheetTextEdit.__CLOSING_CHARS
            and self.__character_at_cursor() == text
        ):
            cursor: QTextCursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Right)
            self.setTextCursor(cursor)
            return

        if event.key() == Qt.Key.Key_Backspace and self.__delete_empty_pair():
            return

        super().keyPressEvent(event)

    def __insert_pair(self, opening: str, closing: str) -> None:
        """
        Inserts matching characters around the selection or cursor.

        Args:
            opening (str): Opening character to insert.
            closing (str): Matching closing character to insert.
        """

        cursor: QTextCursor = self.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(f"{opening}{selected}{closing}")
            return

        cursor.insertText(opening + closing)
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        self.setTextCursor(cursor)

    def __insert_newline(self) -> None:
        cursor: QTextCursor = self.textCursor()
        block_text: str = cursor.block().text()
        position_in_block: int = cursor.positionInBlock()
        before: str = block_text[:position_in_block]
        after: str = block_text[position_in_block:]
        base_indent: str = before[: len(before) - len(before.lstrip(" \t"))]

        if before.rstrip().endswith("{") and after.lstrip().startswith("}"):
            cursor.insertText("\n" + base_indent + self.indent_text + "\n" + base_indent)
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        else:
            extra: str = self.indent_text if before.rstrip().endswith("{") else ""
            cursor.insertText("\n" + base_indent + extra)

        self.setTextCursor(cursor)

    def __change_indentation(self, remove: bool) -> None:
        """
        Adds or removes indentation for the current line or selection.

        Args:
            remove (bool): Whether indentation should be removed.
        """

        cursor: QTextCursor = self.textCursor()
        if not cursor.hasSelection():
            if remove:
                block_text: str = cursor.block().text()
                removable: str = (
                    "\t"
                    if block_text.startswith("\t")
                    else " "
                    * min(
                        self.__indent_size, len(block_text) - len(block_text.lstrip(" "))
                    )
                )
                if removable:
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        len(removable),
                    )
                    cursor.removeSelectedText()
            else:
                cursor.insertText(self.indent_text)
            return

        start: int = cursor.selectionStart()
        end: int = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        first_block: int = cursor.blockNumber()
        cursor.setPosition(end)
        if cursor.positionInBlock() == 0 and end > start:
            cursor.movePosition(QTextCursor.MoveOperation.PreviousBlock)

        last_block: int = cursor.blockNumber()

        edit_cursor = QTextCursor(self.document())
        edit_cursor.beginEditBlock()
        for block_number in range(first_block, last_block + 1):
            block: QTextBlock = self.document().findBlockByNumber(block_number)
            edit_cursor.setPosition(block.position())
            if remove:
                text: str = block.text()
                count: int = (
                    1
                    if text.startswith("\t")
                    else min(self.__indent_size, len(text) - len(text.lstrip(" ")))
                )
                if count:
                    edit_cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        count,
                    )
                    edit_cursor.removeSelectedText()

            else:
                edit_cursor.insertText(self.indent_text)

        edit_cursor.endEditBlock()

    def __delete_empty_pair(self) -> bool:
        """
        Deletes a matching empty pair adjacent to the cursor.

        Returns:
            bool: Whether an empty pair was deleted.
        """

        cursor: QTextCursor = self.textCursor()
        if cursor.hasSelection() or cursor.position() == 0:
            return False

        document_text: str = self.toPlainText()
        position: int = cursor.position()
        before: str = document_text[position - 1 : position]
        after: str = document_text[position : position + 1]
        if StylesheetTextEdit.__OPENING_PAIRS.get(before) != after:
            return False

        cursor.movePosition(QTextCursor.MoveOperation.Left)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 2
        )
        cursor.removeSelectedText()
        self.setTextCursor(cursor)
        return True

    def __character_at_cursor(self) -> str:
        """
        Returns the character immediately after the cursor.

        Returns:
            str: The selected next character, if any.
        """

        cursor: QTextCursor = self.textCursor()
        cursor.movePosition(
            QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor
        )
        return cursor.selectedText()

    def __emit_cursor_position(self) -> None:
        cursor: QTextCursor = self.textCursor()
        self.cursorPositionInfoChanged.emit(
            cursor.blockNumber() + 1, cursor.positionInBlock() + 1
        )

    def __update_extra_selections(self) -> None:
        selections: list[QTextEdit.ExtraSelection] = []
        current_line = QTextEdit.ExtraSelection()
        theme: Theme = ThemeManager.get().theme
        current_line.format.setBackground(
            QColor(theme.resolve(theme.colors.bg_elevated))
        )
        current_line.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        current_line.cursor = self.textCursor()
        current_line.cursor.clearSelection()
        selections.append(current_line)
        selections.extend(self.__bracket_selections())
        self.setExtraSelections(selections)

    def __bracket_selections(self) -> Iterable[QTextEdit.ExtraSelection]:
        """
        Returns selections for a matching pair near the cursor.

        Returns:
            Iterable[QTextEdit.ExtraSelection]: Matching-bracket selections.
        """

        text: str = self.toPlainText()
        cursor_position: int = self.textCursor().position()
        candidates: list[int] = [cursor_position - 1, cursor_position]
        reverse_pairs = {
            value: key for key, value in StylesheetTextEdit.__BRACKET_PAIRS.items()
        }

        for position in candidates:
            if not 0 <= position < len(text):
                continue

            match_position = StylesheetTextEdit.__find_matching_bracket(
                text, position, StylesheetTextEdit.__BRACKET_PAIRS, reverse_pairs
            )
            if match_position is None:
                continue

            return [
                self.__bracket_selection(position),
                self.__bracket_selection(match_position),
            ]

        return []

    @staticmethod
    def __find_matching_bracket(
        text: str,
        position: int,
        pairs: dict[str, str],
        reverse_pairs: dict[str, str],
    ) -> Optional[int]:
        """
        Finds the matching bracket for the character at a text position.

        Args:
            text (str): Complete editor text.
            position (int): Position of the bracket to match.
            pairs (dict[str, str]): Opening-to-closing bracket pairs.
            reverse_pairs (dict[str, str]): Closing-to-opening bracket pairs.

        Returns:
            Optional[int]: Position of the matching bracket, if one exists.
        """

        character: str = text[position]
        opening: str
        closing: str
        direction: int
        if character in pairs:
            opening, closing, direction = character, pairs[character], 1
        elif character in reverse_pairs:
            opening, closing, direction = reverse_pairs[character], character, -1
        else:
            return None

        depth: int = 0
        index: int = position
        while 0 <= index < len(text):
            current: str = text[index]

            if current == opening:
                depth += 1 if direction == 1 else -1
            elif current == closing:
                depth += -1 if direction == 1 else 1

            if depth == 0 and index != position:
                return index

            index += direction

        return None

    def __bracket_selection(self, position: int) -> QTextEdit.ExtraSelection:
        """
        Creates a selection that highlights one bracket.

        Args:
            position (int): Position of the bracket to highlight.

        Returns:
            QTextEdit.ExtraSelection: Bracket highlight selection.
        """

        selection = QTextEdit.ExtraSelection()
        theme: Theme = ThemeManager.get().theme
        selection.format.setBackground(QColor(theme.resolve(theme.colors.warning_bg)))
        cursor = QTextCursor(self.document())
        cursor.setPosition(position)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor
        )
        selection.cursor = cursor
        return selection

    def __on_theme_changed(self, theme: Theme) -> None:
        """
        Updates editor-specific painting after a theme change.

        Args:
            theme (Theme): Newly active application theme.
        """

        self.setFont(theme.texts.monospace.as_qfont())
        self.__highlighter.update_theme(theme)
        self.__update_extra_selections()
