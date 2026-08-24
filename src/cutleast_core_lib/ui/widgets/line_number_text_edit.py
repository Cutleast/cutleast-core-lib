"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from typing import Optional, override

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QPainter, QPaintEvent, QPalette, QResizeEvent, QTextBlock
from PySide6.QtWidgets import QPlainTextEdit, QStyle, QStyleOption, QWidget


class LineNumberTextEdit(QPlainTextEdit):
    """
    QPlainTextEdit with a QSS-styleable line-number gutter.

    The gutter can be addressed with the following QSS selector::

        LineNumberTextEdit QWidget#line_number_area {
            background-color: #202020;
            border-right: 1px solid #3a3a3a;
            color: #a0a0a0;
        }

    Its background and border are rendered through the current Qt style. The
    line-number colors use the gutter's QPalette Text and PlaceholderText roles.
    """

    class _LineNumberArea(QWidget):
        """
        QSS-styleable line-number gutter for a LineNumberTextEdit.
        """

        __editor: LineNumberTextEdit

        @override
        def __init__(self, editor: LineNumberTextEdit) -> None:
            super().__init__(editor)

            self.__editor = editor

            self.setObjectName("line_number_area")
            self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        @override
        def sizeHint(self) -> QSize:
            return QSize(self.__editor._line_number_area_width(), 0)

        @override
        def paintEvent(self, event: QPaintEvent) -> None:
            self.__editor._paint_line_number_area(self, event)

    GUTTER_HORIZONTAL_PADDING: int = 20
    """Horizontal padding included in the gutter width, in pixels."""

    GUTTER_RIGHT_PADDING: int = 15
    """Right padding between line numbers and the gutter edge, in pixels."""

    __line_number_area: _LineNumberArea

    @override
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__line_number_area = LineNumberTextEdit._LineNumberArea(self)
        self.__update_line_number_area_width()

        self.blockCountChanged.connect(self.__update_line_number_area_width)
        self.updateRequest.connect(self.__update_line_number_area)
        self.cursorPositionChanged.connect(self.__update_line_number_area_for_cursor)

    def _line_number_area_width(self) -> int:
        digits: int = max(1, len(str(self.blockCount())))

        return (
            LineNumberTextEdit.GUTTER_HORIZONTAL_PADDING
            + self.fontMetrics().horizontalAdvance("9") * digits
        )

    def _paint_line_number_area(self, area: QWidget, event: QPaintEvent) -> None:
        painter = QPainter(area)
        option = QStyleOption()
        option.initFrom(area)
        area.style().drawPrimitive(
            QStyle.PrimitiveElement.PE_Widget, option, painter, area
        )

        block: QTextBlock = self.firstVisibleBlock()
        block_number: int = block.blockNumber()
        top: int = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom: int = top + round(self.blockBoundingRect(block).height())
        event_rect: QRect = event.rect()

        while block.isValid() and top <= event_rect.bottom():
            if block.isVisible() and bottom >= event_rect.top():
                color_role: QPalette.ColorRole = (
                    QPalette.ColorRole.Text
                    if block_number == self.textCursor().blockNumber()
                    else QPalette.ColorRole.PlaceholderText
                )
                painter.setPen(area.palette().color(color_role))
                painter.setFont(self.font())
                painter.drawText(
                    0,
                    top,
                    area.width() - LineNumberTextEdit.GUTTER_RIGHT_PADDING,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        contents: QRect = self.contentsRect()
        self.__line_number_area.setGeometry(
            QRect(
                contents.left(),
                contents.top(),
                self._line_number_area_width(),
                contents.height(),
            )
        )

    def __update_line_number_area_width(self, _block_count: int = 0) -> None:
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def __update_line_number_area(self, rect: QRect, vertical_delta: int) -> None:
        if vertical_delta:
            self.__line_number_area.scroll(0, vertical_delta)
        else:
            self.__line_number_area.update(
                0, rect.y(), self.__line_number_area.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.__update_line_number_area_width()

    def __update_line_number_area_for_cursor(self) -> None:
        self.__line_number_area.update()
