"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import Property, QByteArray, QMimeData, QPoint, Qt
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from cutleast_core_lib.core.utilities.typing_utils import not_none
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider

from .consts import FLEX_MIME_TYPE


class DragHandle(QLabel):
    """
    A narrow clickable strip rendered in the tile header that initiates a drag-and-drop
    operation when the user drags it.
    """

    DEFAULT_HANDLE_SIZE: int = 12

    __handle_size: int
    __press_pos: Optional[QPoint]
    __content_identifier: str

    def __init__(
        self, content_identifier: str, parent: Optional[QWidget] = None
    ) -> None:
        """
        Args:
            content_identifier (str): The identifier of the panel being dragged.
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__handle_size = DragHandle.DEFAULT_HANDLE_SIZE
        self.__press_pos = None
        self.__content_identifier = content_identifier

        self.setPixmap(
            IconProvider.get_qta_icon("mdi6.drag").pixmap(
                self.__handle_size, self.__handle_size
            )
        )
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFixedSize(self.__handle_size, self.__handle_size)
        self.setToolTip(self.tr("Drag to rearrange"))

    @Property(int)
    def handleSize(self) -> int:  # pyright: ignore[reportRedeclaration]
        """The size of the drag handle in pixels."""

        return self.__handle_size

    @handleSize.setter
    def handleSize(self, size: int) -> None:
        self.__handle_size = size

        self.setPixmap(
            IconProvider.get_qta_icon("mdi6.drag").pixmap(
                self.__handle_size, self.__handle_size
            )
        )
        self.setFixedSize(size, size)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.__press_pos = event.pos()

        super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.__press_pos = None

        super().mouseReleaseEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.__press_pos is None or not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return

        delta = (event.pos() - self.__press_pos).manhattanLength()
        if delta < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        self.__press_pos = None
        self.__start_drag()

    def __start_drag(self) -> None:
        mime = QMimeData()
        mime.setData(FLEX_MIME_TYPE, QByteArray(self.__content_identifier.encode()))

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(not_none(self.parentWidget()).grab())
        drag.exec(Qt.DropAction.MoveAction)
