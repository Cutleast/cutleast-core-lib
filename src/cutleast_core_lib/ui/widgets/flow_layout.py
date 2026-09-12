"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import QMargins, QObject, QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QLayoutItem, QSizePolicy, QStyle, QWidget


class FlowLayout(QLayout):
    """
    Layout that arranges items in rows and wraps them to the available width.
    """

    __items: list[QLayoutItem]
    __horizontal_spacing: int
    __vertical_spacing: int

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        margin: int = -1,
        horizontal_spacing: int = -1,
        vertical_spacing: int = -1,
    ) -> None:
        """
        Args:
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
            margin (int, optional): Layout margin. Defaults to the style value.
            horizontal_spacing (int, optional):
                Horizontal spacing between items. Defaults to the style value.
            vertical_spacing (int, optional):
                Vertical spacing between rows. Defaults to the style value.
        """

        super().__init__(parent)

        self.__items = []
        self.__horizontal_spacing = horizontal_spacing
        self.__vertical_spacing = vertical_spacing

        self.setContentsMargins(margin, margin, margin, margin)

    @override
    def addItem(self, item: QLayoutItem, /) -> None:
        self.__items.append(item)

    def horizontalSpacing(self) -> int:
        """
        Returns:
            int: Horizontal spacing between layout items.
        """

        if self.__horizontal_spacing >= 0:
            return self.__horizontal_spacing

        return self.__smart_spacing(QStyle.PixelMetric.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self) -> int:
        """
        Returns:
            int: Vertical spacing between layout rows.
        """

        if self.__vertical_spacing >= 0:
            return self.__vertical_spacing

        return self.__smart_spacing(QStyle.PixelMetric.PM_LayoutVerticalSpacing)

    @override
    def count(self) -> int:
        return len(self.__items)

    @override
    def itemAt(self, index: int, /) -> Optional[QLayoutItem]:
        if 0 <= index < len(self.__items):
            return self.__items[index]

        return None

    @override
    def takeAt(self, index: int, /) -> Optional[QLayoutItem]:
        if 0 <= index < len(self.__items):
            return self.__items.pop(index)

        return None

    @override
    def removeWidget(self, widget: QWidget, /) -> None:
        for index, item in enumerate(self.__items):
            if item.widget() is widget:
                self.takeAt(index)
                widget.hide()
                self.invalidate()
                return

    @override
    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    @override
    def hasHeightForWidth(self) -> bool:
        return True

    @override
    def heightForWidth(self, width: int, /) -> int:
        return self.__do_layout(QRect(0, 0, width, 0), True)

    @override
    def setGeometry(self, rect: QRect, /) -> None:
        super().setGeometry(rect)

        self.__do_layout(rect, False)

    @override
    def sizeHint(self) -> QSize:
        return self.minimumSize()

    @override
    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self.__items:
            if item.isEmpty():
                continue

            size = size.expandedTo(item.minimumSize())

        margins: QMargins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

        return size

    def __do_layout(self, rect: QRect, test_only: bool) -> int:
        """
        Calculates item positions and optionally applies their geometry.

        Args:
            rect (QRect): Available layout geometry.
            test_only (bool): Whether to calculate without changing item geometry.

        Returns:
            int: Height required by the arranged items.
        """

        margins: QMargins = self.contentsMargins()
        effective_rect: QRect = rect.adjusted(
            margins.left(), margins.top(), -margins.right(), -margins.bottom()
        )
        x: int = effective_rect.x()
        y: int = effective_rect.y()
        line_height: int = 0

        for item in self.__items:
            if item.isEmpty():
                continue

            horizontal_spacing: int = self.horizontalSpacing()
            vertical_spacing: int = self.verticalSpacing()
            widget: Optional[QWidget] = item.widget()

            if horizontal_spacing == -1 and widget is not None:
                horizontal_spacing = widget.style().layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Horizontal,
                )
            if vertical_spacing == -1 and widget is not None:
                vertical_spacing = widget.style().layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Vertical,
                )

            item_size: QSize = item.sizeHint()
            next_x: int = x + item_size.width() + horizontal_spacing
            if next_x - horizontal_spacing > effective_rect.right() and line_height:
                x = effective_rect.x()
                y += line_height + vertical_spacing
                next_x = x + item_size.width() + horizontal_spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item_size))

            x = next_x
            line_height = max(line_height, item_size.height())

        return y + line_height - rect.y() + margins.bottom()

    def __smart_spacing(self, pixel_metric: QStyle.PixelMetric) -> int:
        """
        Resolves layout spacing from the parent widget or layout.

        Args:
            pixel_metric (QStyle.PixelMetric): Style metric to resolve.

        Returns:
            int: Resolved spacing, or `-1` if no parent supplies one.
        """

        parent: Optional[QObject] = self.parent()
        if isinstance(parent, QWidget):
            return parent.style().pixelMetric(pixel_metric, None, parent)
        if isinstance(parent, QLayout):
            return parent.spacing()

        return -1
