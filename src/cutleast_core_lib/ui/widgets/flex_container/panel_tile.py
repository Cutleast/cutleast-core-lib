"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, override

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QResizeEvent,
)
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .consts import FLEX_MIME_TYPE
from .drag_handle import DragHandle
from .drop_indicator import DropIndicator
from .drop_zone import DropZone
from .flex_content import FlexContent

if TYPE_CHECKING:
    from .flex_container import FlexContainer


class PanelTile(QWidget):
    """
    Wrapper widget that surrounds a `FlexContent` panel with a title-bar header
    containing the drag handle and the panel's title, and manages the visual drop
    indicator during drag-and-drop operations.
    """

    __root_container: FlexContainer
    __content: FlexContent
    __drop_indicator: DropIndicator
    __drag_handle: DragHandle

    def __init__(
        self,
        content: FlexContent,
        root_container: FlexContainer,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            content (FlexContent): The panel widget.
            root_container (FlexContainer):
                The top-level `FlexContainer` that owns this tile. Used to delegate drop
                operations.
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__root_container = root_container
        self.__content = content

        self.__init_ui()

    def __init_ui(self) -> None:
        self.setAcceptDrops(True)

        outer_vlayout = QVBoxLayout()
        outer_vlayout.setContentsMargins(0, 0, 0, 0)
        outer_vlayout.setSpacing(0)
        self.setLayout(outer_vlayout)

        header_widget = QWidget()
        header_widget.setObjectName("flex_tile_header")
        outer_vlayout.addWidget(header_widget)

        header_hlayout = QHBoxLayout()
        header_hlayout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        header_widget.setLayout(header_hlayout)

        self.__drag_handle = DragHandle(self.content_identifier, self)
        header_hlayout.addWidget(self.__drag_handle)

        title_label = QLabel(self.content_title)
        title_label.setObjectName("flex_tile_title")
        header_hlayout.addWidget(title_label)

        outer_vlayout.addWidget(self.__content, stretch=1)

        self.__drop_indicator = DropIndicator(self)
        self.__drop_indicator.resize(self.size())

    @property
    def content_identifier(self) -> str:
        """
        The identifier of the wrapped panel, as returned by
        `FlexContent.get_identifier()`.
        """

        return self.__content.get_identifier()

    @property
    def content_title(self) -> str:
        """The title of the wrapped content, as returned by `FlexContent.get_title()`."""

        return self.__content.get_title()

    @property
    def content(self) -> FlexContent:
        """The wrapped content widget."""

        return self.__content

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.__drop_indicator.resize(event.size())

        super().resizeEvent(event)

    @override
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(FLEX_MIME_TYPE):
            source_id: str = event.mimeData().data(FLEX_MIME_TYPE).toStdString()

            if source_id != self.content_identifier:
                event.acceptProposedAction()
                return

        event.ignore()

    @override
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if not event.mimeData().hasFormat(FLEX_MIME_TYPE):
            event.ignore()
            return

        zone: DropZone = DropZone.from_pos(
            x=event.position().toPoint().x(),
            y=event.position().toPoint().y(),
            width=self.width(),
            height=self.height(),
        )
        self.__drop_indicator.setZone(zone)
        event.acceptProposedAction()

    @override
    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.__drop_indicator.setZone(None)

        super().dragLeaveEvent(event)

    @override
    def dropEvent(self, event: QDropEvent) -> None:
        self.__drop_indicator.setZone(None)

        if not event.mimeData().hasFormat(FLEX_MIME_TYPE):
            event.ignore()
            return

        source_id: str = event.mimeData().data(FLEX_MIME_TYPE).toStdString()
        zone: DropZone = DropZone.from_pos(
            x=event.position().toPoint().x(),
            y=event.position().toPoint().y(),
            width=self.width(),
            height=self.height(),
        )

        if zone is not DropZone.Center and source_id != self.content_identifier:
            self.__root_container.movePanel(source_id, self.content_identifier, zone)
            event.acceptProposedAction()
        else:
            event.ignore()
