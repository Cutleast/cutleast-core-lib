"""
Copyright (c) Cutleast
"""

from typing import Optional, cast, override

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QMimeData,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QSizeF,
    Qt,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QDrag,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPixmap,
    QRegion,
)
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyleOption,
    QStyleOptionTab,
    QTabBar,
    QToolButton,
    QWidget,
)
from shiboken6 import isValid


class AnimatedTabBar(QTabBar):
    """
    Animates tab snapshots around an insertion gap without changing the real tab order.
    """

    __prepared: bool
    __source_index: Optional[int]
    __count: int
    __drag_extent: float
    __base: list[QRectF]
    __pixmaps: list[QPixmap]
    __scroll_region: QRegion
    __scroll_pixmap: QPixmap
    __rectangles: list[QRectF]
    __start: list[QRectF]
    __end: list[QRectF]
    __index: Optional[int]
    __masks: dict[QWidget, QRegion]
    __indices: list[int]
    __direction: QPointF
    __incoming_source: Optional[AnimatedTabBar]
    __target_bar: Optional[AnimatedTabBar]
    __press_position: Optional[QPoint]
    __native_press_position: Optional[QPointF]
    __press_index: int
    __drag: Optional[QDrag]
    __destination: Optional[int]
    __animation: QVariantAnimation

    dragStarted = Signal(int, QDrag)
    """
    Allows synchronous MIME configuration before the bar runs its own drag loop.

    Args:
        int: Source index in the original order.
        QDrag: Prepared drag owned by this bar, with its native cursor pixmap.
    """

    dragFinished = Signal(int, Qt.DropAction)
    """
    Reports completion after source feedback and native pressed state are restored.

    Handlers may now transfer pages or replace the bar. Local reordering commits
    moveTab before emitting this signal. IgnoreAction also reports cancellation.

    Args:
        int: Original source index.
        Qt.DropAction: Native drag result.
    """

    dragEntered = Signal(QDragEnterEvent)
    """
    Lets the application accept compatible incoming tab drags synchronously.

    Args:
        QDragEnterEvent: Incoming event; ignored unless a handler accepts it.
    """

    dropRequested = Signal(int, QDropEvent)
    """
    Requests an incoming transfer at a stable insertion boundary.

    Accept the event synchronously, but defer content mutations until the source
    emits drag_finished. Local drops reorder internally without this signal.

    Args:
        int: Insertion boundary in the destination's current native order.
        QDropEvent: Incoming event; ignored unless a handler accepts it.
    """

    @override
    def __init__(self, parent: Optional[QWidget] = None, *, duration: int = 140) -> None:
        """
        Args:
            parent (Optional[QWidget]): Optional parent widget. Defaults to None.
            duration (int): Gap transition duration in milliseconds. Defaults to 140.

        Raises:
            ValueError: Duration is negative.
        """

        if duration < 0:
            raise ValueError("Animation duration must be nonnegative.")

        # Qt may dispatch events while constructing the underlying widget.
        self.__prepared = False
        self.__drag = None
        self.__incoming_source = None
        self.__target_bar = None
        self.__source_index = None
        self.__count = 0
        self.__drag_extent = 0
        self.__base = []
        self.__pixmaps = []
        self.__scroll_region = QRegion()
        self.__scroll_pixmap = QPixmap()
        self.__rectangles = []
        self.__start = []
        self.__end = []
        self.__index = -1
        self.__masks = {}
        self.__indices = []
        self.__direction = QPointF(1, 0)
        self.__press_position = None
        self.__native_press_position = None
        self.__press_index = -1
        self.__destination = None

        super().__init__(parent)

        self.setMovable(True)
        self.setAcceptDrops(True)

        self.__animation = QVariantAnimation(self)
        self.__animation.setDuration(duration)
        self.__animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.__animation.valueChanged.connect(self.__advance)

        self.tabMoved.connect(self.__cancel_preview)

    def __prepare_drag(self, extent: float, source_index: Optional[int] = None) -> None:
        """
        Captures tabs without changing selection, order, button geometry or effects.

        Args:
            extent (float): Dragged tab size along the bar's layout axis.
            source_index (Optional[int]): Tab to exclude; None for an external tab.

        Raises:
            ValueError: Extent is nonpositive or the source index is invalid/hidden.
        """

        if extent <= 0:
            raise ValueError("The dragged tab extent must be positive.")
        
        if source_index is not None and (
            not 0 <= source_index < self.count() or not self.isTabVisible(source_index)
        ):
            raise ValueError("The source must be an existing visible tab.")

        if (
            self.__is_prepared
            and extent == self.__drag_extent
            and source_index == self.__source_index
        ):
            return

        self.__clear_feedback()
        self.__drag_extent = extent
        self.__source_index = source_index
        self.__count = self.count()
        self.__direction = self.__layout_direction()
        source_extent: float = (
            0
            if source_index is None
            else self.__extent(QRectF(self.tabRect(source_index)))
        )
        tab_buttons: list[QWidget] = []
        for index in range(self.count()):
            for side in (
                QTabBar.ButtonPosition.LeftSide,
                QTabBar.ButtonPosition.RightSide,
            ):
                # A tab may itself contain tool buttons; those must move with the tab.
                button = cast(Optional[QWidget], self.tabButton(index, side))
                if button is not None:
                    tab_buttons.append(button)

        scroll_buttons: list[QToolButton] = []
        for button in self.findChildren(QToolButton):
            if not button.isHidden() and not any(
                tab_button is button or tab_button.isAncestorOf(button)
                for tab_button in tab_buttons
            ):
                scroll_buttons.append(button)
                self.__scroll_region |= QRegion(
                    QRect(button.mapTo(self, QPoint()), button.size())
                )

        if scroll_buttons:
            effect = self.graphicsEffect()
            enabled: bool = effect is not None and effect.isEnabled()
            if enabled and effect is not None:
                effect.setEnabled(False)
            try:
                self.__scroll_pixmap = self.grab()
            finally:
                if enabled and effect is not None:
                    effect.setEnabled(True)

        for index in range(self.count()):
            if index == source_index or not self.isTabVisible(index):
                continue

            rectangle = QRectF(self.tabRect(index))
            self.__indices.append(index)
            self.__rectangles.append(QRectF(rectangle))
            if source_index is not None and index > source_index:
                rectangle.translate(-self.__direction * source_extent)

            self.__base.append(rectangle)
            self.__pixmaps.append(self.__grab_tab(index))

        for button in [*tab_buttons, *scroll_buttons]:
            self.__masks[button] = button.mask()
            # An outside mask suppresses child painting without triggering tab relayout.
            button.setMask(QRegion(QRect(-1, -1, 1, 1)))

        self.__prepared = True
        self.update()

    def __layout_direction(self) -> QPointF:
        """
        Resolves logical tab order for horizontal, vertical and right-to-left bars.

        Returns:
            QPointF: Unit vector pointing towards increasing tab indices.
        """

        if self.shape() in (
            QTabBar.Shape.RoundedWest,
            QTabBar.Shape.RoundedEast,
            QTabBar.Shape.TriangularWest,
            QTabBar.Shape.TriangularEast,
        ):
            return QPointF(0, 1)

        return QPointF(-1 if self.isRightToLeft() else 1, 0)

    def __grab_tab(self, index: int) -> QPixmap:
        """
        Renders a native styled tab and its buttons with transparent corners.

        Args:
            index (int): Existing visible tab index.

        Returns:
            QPixmap: Native tab snapshot preserving its device pixel ratio.

        Raises:
            ValueError: The index is invalid or hidden.
        """

        if not 0 <= index < self.count() or not self.isTabVisible(index):
            raise ValueError("The snapshot requires an existing visible tab.")

        rectangle: QRect = self.tabRect(index)
        pixel_ratio: float = self.devicePixelRatioF()
        pixmap = QPixmap(
            round(rectangle.width() * pixel_ratio),
            round(rectangle.height() * pixel_ratio),
        )
        pixmap.setDevicePixelRatio(pixel_ratio)
        pixmap.fill(Qt.GlobalColor.transparent)
        option = QStyleOptionTab()
        self.initStyleOption(option, index)
        painter = QPainter(pixmap)
        # Stylesheet label layout uses the bar's original coordinates.
        painter.save()
        painter.translate(-rectangle.topLeft())
        self.style().drawControl(
            QStyle.ControlElement.CE_TabBarTab, option, painter, self
        )
        painter.restore()
        for side in (QTabBar.ButtonPosition.LeftSide, QTabBar.ButtonPosition.RightSide):
            # Qt returns nullptr when this side has no button; the stub omits None.
            button = cast(Optional[QWidget], self.tabButton(index, side))
            if button is not None:
                mask: Optional[QRegion] = self.__masks.get(button)
                if mask is not None:
                    button.setMask(mask)
                try:
                    button.render(
                        painter,
                        button.pos() - rectangle.topLeft(),
                        QRegion(),
                        QWidget.RenderFlag.DrawChildren,
                    )
                finally:
                    if mask is not None:
                        button.setMask(QRegion(QRect(-1, -1, 1, 1)))

        painter.end()
        return pixmap

    def __insertion_index(self, global_position: QPoint) -> int:
        """
        Selects the nearest gap center without using moving tab coordinates.

        Args:
            global_position (QPoint): Pointer in screen coordinates.

        Returns:
            int: Insertion boundary in the original tab order, before source removal.
        """

        position = QPointF(self.mapFromGlobal(global_position))
        ordinal: int = sum(
            self.__project(position)
            > self.__project(rectangle.center()) + self.__drag_extent / 2
            for rectangle in self.__base
        )
        if ordinal < len(self.__indices):
            return self.__indices[ordinal]

        return self.count()

    @property
    def __is_prepared(self) -> bool:
        """Whether the current tabs still match the captured tab count."""

        return self.__prepared and self.count() == self.__count

    def __set_insertion(self, index: Optional[int]) -> None:
        """
        Animates the insertion gap or closes the source slot when dragged elsewhere.

        Args:
            index (Optional[int]): Original insertion index; None closes the gap.

        Raises:
            ValueError: The insertion boundary is outside the current tab order.
        """

        if index is not None and not 0 <= index <= self.count():
            raise ValueError("The insertion boundary must be between zero and count().")

        if not self.__is_prepared or index == self.__index:
            return

        self.__index = index
        self.__animation.stop()
        self.__start = [QRectF(rectangle) for rectangle in self.__rectangles]
        self.__end = [QRectF(rectangle) for rectangle in self.__base]
        if index is not None:
            slot: int = self.__slot(index)
            for rectangle in self.__end[slot:]:
                rectangle.translate(self.__direction * self.__drag_extent)

        self.__animation.setStartValue(0.0)
        self.__animation.setEndValue(1.0)
        self.__animation.start()

    def __clear_feedback(self) -> None:
        """
        Restores the real bar and releases preview data after leave, drop or cancellation.
        """

        was_prepared: bool = self.__prepared
        self.__animation.stop()
        for button, mask in self.__masks.items():
            if isValid(button):
                button.setMask(mask)

        self.__masks.clear()
        source: Optional[AnimatedTabBar] = self.__incoming_source
        self.__incoming_source = None
        if source is not None and source.__target_bar is self:
            source.__target_bar = None

        self.__prepared = False
        self.__indices.clear()
        self.__index = -1
        self.__base.clear()
        self.__pixmaps.clear()
        self.__scroll_region = QRegion()
        self.__scroll_pixmap = QPixmap()
        self.__rectangles.clear()
        if was_prepared and self.__native_press_position is not None:
            # QDrag can consume the release; reset Qt's pressed-tab state before commit.
            position: QPointF = self.__native_press_position
            self.__native_press_position = None
            release = QMouseEvent(
                QEvent.Type.MouseButtonRelease,
                position,
                QPointF(self.mapToGlobal(position.toPoint())),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )
            super().mouseReleaseEvent(release)

        self.update()

    def __slot(self, index: int) -> int:
        """
        Converts an original insertion index to the order without the dragged tab.

        Args:
            index (int): Original insertion boundary.

        Returns:
            int: Boundary after excluding the source tab.
        """

        return sum(candidate < index for candidate in self.__indices)

    def __project(self, point: QPointF) -> float:
        """
        Projects a position onto the increasing-index layout axis.

        Args:
            point (QPointF): Local coordinate.

        Returns:
            float: Signed position along the bar.
        """

        return point.x() * self.__direction.x() + point.y() * self.__direction.y()

    def __extent(self, rectangle: QRectF) -> float:
        """
        Reads a tab's size along the layout axis.

        Args:
            rectangle (QRectF): Native tab rectangle.

        Returns:
            float: Width for horizontal bars, height for vertical bars.
        """

        return rectangle.height() if self.__direction.y() else rectangle.width()

    def __cancel_preview(self) -> None:
        """
        Cancels stale local feedback before tab order or widget geometry changes.
        """

        self.__destination = None
        if self.__drag is not None:
            QDrag.cancel()

        if self.__prepared:
            self.__clear_feedback()

    @override
    def event(self, event: QEvent) -> bool:
        if self.__prepared and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Move,
            QEvent.Type.Hide,
            QEvent.Type.StyleChange,
            QEvent.Type.LayoutDirectionChange,
            QEvent.Type.DeferredDelete,
        ):
            self.__cancel_preview()

        return super().event(event)

    @override
    def tabInserted(self, index: int) -> None:
        self.__cancel_preview()
        super().tabInserted(index)

    @override
    def tabRemoved(self, index: int) -> None:
        self.__cancel_preview()
        super().tabRemoved(index)

    def __advance(self, progress: float) -> None:
        """
        Retargets from current painted positions without affecting logical hit testing.

        Args:
            progress (float): Eased interpolation progress from zero to one.
        """

        self.__rectangles = [
            QRectF(
                start.topLeft() + (end.topLeft() - start.topLeft()) * progress, end.size()
            )
            for start, end in zip(self.__start, self.__end, strict=True)
        ]
        self.update()

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        if not self.__is_prepared:
            if self.__prepared:
                self.__clear_feedback()
            super().paintEvent(event)
            return

        painter = QPainter(self)
        option = QStyleOption()
        option.initFrom(self)
        self.style().drawPrimitive(
            QStyle.PrimitiveElement.PE_Widget, option, painter, self
        )
        painter.setClipRegion(QRegion(self.rect()) - self.__scroll_region)
        for rectangle, pixmap in zip(self.__rectangles, self.__pixmaps, strict=True):
            painter.drawPixmap(rectangle.topLeft(), pixmap)
            
        if not self.__scroll_region.isEmpty():
            painter.setClipRegion(self.__scroll_region)
            painter.drawPixmap(QPoint(), self.__scroll_pixmap)

        painter.end()

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.__native_press_position = event.position()
            self.__press_position = event.position().toPoint()
            self.__press_index = self.tabAt(self.__press_position)

        super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.__native_press_position = None
        self.__press_position = None
        self.__press_index = -1
        super().mouseReleaseEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (
            self.isMovable()
            and self.__press_position is not None
            and self.__press_index >= 0
            and event.buttons() & Qt.MouseButton.LeftButton
            and (event.position().toPoint() - self.__press_position).manhattanLength()
            >= QApplication.startDragDistance()
        ):
            index: int = self.__press_index
            self.__press_position = None
            self.__press_index = -1
            self.__start_drag(index)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def __start_drag(self, index: int) -> None:
        """
        Runs the drag and restores source visuals before committing or notifying owners.

        Args:
            index (int): Source tab in the original order.
        """

        if self.__drag is not None:
            return

        pixmap: QPixmap = self.__grab_tab(index)
        size: QSizeF = pixmap.deviceIndependentSize()
        extent: float = size.height() if self.__layout_direction().y() else size.width()
        drag = QDrag(self)
        self.__drag = drag
        self.__destination = None
        mime = QMimeData()
        mime.setData("application/x-core-tab-reorder", b"")
        drag.setMimeData(mime)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(round(size.width() / 2), round(size.height() / 2)))
        result: Qt.DropAction = Qt.DropAction.IgnoreAction
        try:
            self.__prepare_drag(extent, index)
            # A drag may begin outside the bar before any enter/leave event arrives.
            self.__set_insertion(None)
            self.dragStarted.emit(index, drag)
            result = drag.exec(Qt.DropAction.MoveAction)
        finally:
            destination: Optional[int] = self.__destination
            self.__destination = None
            target: Optional[AnimatedTabBar] = self.__target_bar
            self.__target_bar = None
            if target is not None and isValid(target):
                target.__clear_feedback()

            if isValid(self):
                self.__clear_feedback()

            self.__drag = None
            if isValid(drag):
                drag.deleteLater()

            if isValid(self):
                if result == Qt.DropAction.MoveAction and destination is not None:
                    self.moveTab(index, destination - int(index < destination))

                self.dragFinished.emit(index, result)

    def __drag_source(self, event: QDropEvent) -> Optional[AnimatedTabBar]:
        """
        Recognizes a live compatible tab drag without application-specific metadata.

        Args:
            event (QDropEvent): Native drag event.

        Returns:
            Optional[AnimatedTabBar]: Live source bar, or None for unrelated drags.
        """

        source = event.source()
        if (
            isinstance(source, AnimatedTabBar)
            and isValid(source)
            and source.__drag is not None
            and event.mimeData().hasFormat("application/x-core-tab-reorder")
        ):
            return source

        return None

    @override
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        source: Optional[AnimatedTabBar] = self.__drag_source(event)
        event.ignore()
        if source is None:
            return

        if source is self:
            if not self.__is_prepared:
                return

            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            self.dragEntered.emit(event)
            if not event.isAccepted():
                return

            size: QSizeF = cast(QDrag, source.__drag).pixmap().deviceIndependentSize()
            extent: float = (
                size.height() if self.__layout_direction().y() else size.width()
            )
            self.__prepare_drag(extent)
            previous: Optional[AnimatedTabBar] = source.__target_bar
            if previous is not None and previous is not self and isValid(previous):
                previous.__clear_feedback()

            self.__incoming_source = source
            source.__target_bar = self
        self.dragMoveEvent(event)

    @override
    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        source: Optional[AnimatedTabBar] = self.__drag_source(event)
        if (
            source is not None
            and (source is self or source is self.__incoming_source)
            and self.__is_prepared
        ):
            self.__set_insertion(
                self.__insertion_index(self.mapToGlobal(event.position().toPoint()))
            )
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    @override
    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        if self.__drag is not None:
            self.__set_insertion(None)
        else:
            self.__clear_feedback()

        event.accept()

    @override
    def dropEvent(self, event: QDropEvent) -> None:
        source: Optional[AnimatedTabBar] = self.__drag_source(event)
        event.ignore()
        if source is None or not self.__is_prepared:
            return

        index: int = self.__insertion_index(self.mapToGlobal(event.position().toPoint()))
        if source is self:
            self.__destination = index
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        elif source is self.__incoming_source:
            try:
                self.dropRequested.emit(index, event)
            finally:
                self.__clear_feedback()
