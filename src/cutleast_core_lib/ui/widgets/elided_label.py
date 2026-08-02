"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import QEvent, QMargins, QSize, Qt
from PySide6.QtGui import QFontMetrics, QResizeEvent
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget


class ElidedLabel(QLabel):
    """
    A QLabel subclass that elides its text with '...' when the widget is too narrow to
    display the full text.
    """

    __full_text: str
    __tooltip_text: Optional[str]
    __elide_mode: Qt.TextElideMode

    def __init__(
        self,
        text: str = "",
        tooltip_text: Optional[str] = None,
        elide_mode: Qt.TextElideMode = Qt.TextElideMode.ElideRight,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            text (str, optional): The full text to display. Defaults to "".
            tooltip_text (Optional[str], optional):
                The text to display in the tooltip. Defaults to None, which
                means the current full text is shown.
            elide_mode (Qt.TextElideMode, optional):
                Where the text is truncated. Defaults to Qt.TextElideMode.ElideRight.
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__full_text = text
        self.__tooltip_text = tooltip_text
        self.__elide_mode = elide_mode

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.__update_elided_text()

    @override
    def text(self) -> str:
        return self.__full_text

    @override
    def setText(self, text: str) -> None:
        self.__full_text = text

        self.__update_elided_text()

    @override
    def setToolTip(self, tooltip_text: Optional[str]) -> None:
        self.__tooltip_text = tooltip_text

        self.__update_elided_text()

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        self.__update_elided_text()

    @override
    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)

        if event.type() == QEvent.Type.FontChange:
            self.__update_elided_text()

    @override
    def sizeHint(self) -> QSize:
        metrics = QFontMetrics(self.font())
        margins: QMargins = self.contentsMargins()
        height: int = metrics.height() + margins.top() + margins.bottom()

        return QSize(0, height)

    @override
    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def __update_elided_text(self) -> None:
        metrics = QFontMetrics(self.font())
        elided: str = metrics.elidedText(
            self.__full_text,
            self.__elide_mode,
            self.width(),
        )

        super().setText(elided)

        tool_tip_text: str = (
            self.__tooltip_text
            if self.__tooltip_text is not None
            else (self.__full_text if elided != self.__full_text else "")
        )

        super().setToolTip(tool_tip_text)
