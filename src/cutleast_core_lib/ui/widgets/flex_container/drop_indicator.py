"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import Property, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from cutleast_core_lib.ui.utilities.theme import HexColorStr

from .drop_zone import DropZone


class DropIndicator(QWidget):
    """
    Transparent overlay widget that draws a coloured line at the edge corresponding to
    the active `DropZone`.

    The overlay is meant to be placed as a child of a panel tile and sized to cover the
    tile completely. It is mouse-transparent so it does not interfere with drag events.
    """

    DEFAULT_INDICATOR_COLOR: HexColorStr = "#0078d7"
    """Default color of the drop-indicator line (a bright blue accent)."""

    DEFAULT_INDICATOR_WIDTH: int = 4
    """Default pixel width (thickness) of the drop-indicator line."""

    __indicator_color: QColor
    __indicator_width: int
    __zone: Optional[DropZone]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__indicator_color = QColor(DropIndicator.DEFAULT_INDICATOR_COLOR)
        self.__indicator_width = DropIndicator.DEFAULT_INDICATOR_WIDTH
        self.__zone = None

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setVisible(False)

    def setZone(self, zone: Optional[DropZone]) -> None:
        """
        Updates the active drop zone and repaints the overlay.

        Passing `None` hides the overlay entirely.

        Args:
            zone (Optional[DropZone]):
                The zone to highlight, or `None` to hide the indicator.
        """

        self.__zone = zone
        self.setVisible(zone is not None)

        if zone is not None:
            self.raise_()
            self.update()

    @Property(str)
    def indicatorColor(self) -> str:  # pyright: ignore[reportRedeclaration]
        """Hex color string of the drop-indicator line."""

        return self.__indicator_color.name()

    @indicatorColor.setter
    def indicatorColor(self, color: str) -> None:
        self.__indicator_color = QColor(color)

        self.update()

    @Property(int)
    def indicatorWidth(self) -> int:  # pyright: ignore[reportRedeclaration]
        """Pixel width (thickness) of the drop-indicator line."""

        return self.__indicator_width

    @indicatorWidth.setter
    def indicatorWidth(self, width: int) -> None:
        self.__indicator_width = width

        self.update()

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        if self.__zone is None or self.__zone is DropZone.Center:
            return

        painter = QPainter(self)
        pen = QPen(self.__indicator_color, self.__indicator_width)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)

        half: int = self.__indicator_width // 2
        w: int = self.width()
        h: int = self.height()

        match self.__zone:
            case DropZone.Left:
                painter.drawLine(half, 0, half, h)
            case DropZone.Right:
                painter.drawLine(w - half, 0, w - half, h)
            case DropZone.Top:
                painter.drawLine(0, half, w, half)
            case DropZone.Bottom:
                painter.drawLine(0, h - half, w, h - half)

        painter.end()
