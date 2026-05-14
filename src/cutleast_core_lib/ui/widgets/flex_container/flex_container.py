"""
Copyright (c) Cutleast
"""

from collections.abc import Mapping, Sequence
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from .drop_zone import DropZone
from .flex_content import FlexContent
from .flex_splitter import FlexChild, FlexSplitter
from .models import LayoutNode, PanelNode, SplitterNode
from .panel_tile import PanelTile

type RootNode = PanelTile | FlexSplitter
"""Type alias for the two possible states of the root node inside a `FlexContainer`."""


class FlexContainer(QWidget):
    """
    A resizable, drag-and-drop-reorderable container widget.

    `FlexContainer` manages a tree of `FlexSplitter` nodes with `PanelTile` leaves.

    The user can:
    * resize panels by dragging splitter handles (standard `QSplitter` behaviour),
    * reorder panels by dragging their tile headers to a new position within the
      container,
    * split the view horizontally or vertically by dragging a tile to a perpendicular
      edge of another tile.

    The current arrangement can be serialized to a `LayoutNode` and later restored via
    `loadLayout()`.
    """

    __root: RootNode
    __vlayout: QVBoxLayout

    def __init__(
        self, panels: Sequence[FlexContent], parent: Optional[QWidget] = None
    ) -> None:
        """
        Args:
            panels (Sequence[FlexContent]): The panel widgets to arrange.
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.

        Raises:
            ValueError: If `panels` is empty.
        """

        super().__init__(parent)

        if not panels:
            raise ValueError("panels must not be empty")

        self.__vlayout = QVBoxLayout()
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__vlayout)

        tiles: list[PanelTile] = [self.__create_tile(p) for p in panels]

        if len(tiles) == 1:
            self.__root = tiles[0]
        else:
            splitter = FlexSplitter(Qt.Orientation.Horizontal, self)
            for tile in tiles:
                splitter.addWidget(tile)
            self.__root = splitter

        self.__vlayout.addWidget(self.__root)

    def __create_tile(self, panel: FlexContent) -> PanelTile:
        """
        Wraps a panel in a panel tile.

        Args:
            panel (FlexContent): The panel content.

        Returns:
            PanelTile: The new tile wrapping `panel`.
        """

        return PanelTile(panel, self)

    def _set_root(self, widget: RootNode) -> None:
        """
        Replaces the current root node with `widget` and updates the layout.

        Args:
            widget (RootNode): The new root node.
        """

        old_root: RootNode = self.__root
        self.__root = widget
        self.__vlayout.replaceWidget(old_root, widget)
        old_root.setParent(None)

    def _find_tile(self, identifier: str) -> Optional[PanelTile]:
        """
        Locates the `PanelTile` with the given panel identifier via depth-first search.

        Args:
            identifier (str): The identifier to search for.

        Returns:
            Optional[PanelTile]: The matching tile or `None` if not found.
        """

        return self.__dfs_find_tile(self.__root, identifier)

    def __dfs_find_tile(self, node: RootNode, identifier: str) -> Optional[PanelTile]:
        """
        Recursive depth-first search for a tile by identifier.

        Args:
            node (RootNode): Current node to inspect.
            identifier (str): The target identifier.

        Returns:
            Optional[PanelTile]: The matching tile or `None`.
        """

        if isinstance(node, PanelTile):
            return node if node.content_identifier == identifier else None

        for child in node.getFlexChildren():
            result: Optional[PanelTile] = self.__dfs_find_tile(child, identifier)
            if result is not None:
                return result

        return None

    def __find_parent(self, tile: PanelTile) -> Optional[FlexSplitter]:
        """
        Returns the direct `FlexSplitter` parent of `tile` or `None` if the tile is the
        root.

        Args:
            tile (PanelTile): The tile whose parent is sought.

        Returns:
            Optional[FlexSplitter]:
                The parent splitter or `None` if `tile` is the root.
        """

        return self.__dfs_find_parent(self.__root, tile)

    def __dfs_find_parent(
        self, node: RootNode, target: PanelTile
    ) -> Optional[FlexSplitter]:
        """
        Recursive helper for `__find_parent()`.

        Args:
            node (RootNode): Current node to inspect.
            target (PanelTile): The tile whose parent is sought.

        Returns:
            Optional[FlexSplitter]: The parent splitter or `None`.
        """

        if isinstance(node, PanelTile):
            return None

        for child in node.getFlexChildren():
            if child is target:
                return node

            if isinstance(child, FlexSplitter):
                result: Optional[FlexSplitter] = self.__dfs_find_parent(child, target)
                if result is not None:
                    return result

        return None

    def movePanel(self, source_id: str, target_id: str, zone: DropZone) -> None:
        """
        Moves the panel identified by `source_id` to the position determined by
        `target_id` and `zone`.

        The method handles all structural cases:
        * **Same orientation** - the source tile is re-inserted before or after the
          target within the same splitter.
        * **Perpendicular orientation** - a new splitter is created around the target
          tile and the source is placed on the appropriate side.
        * **Single-tile root** - a new splitter is created at the root level to
          accommodate both tiles.

        A clean-up pass is run afterwards to remove any splitter that ends up with a single child.

        Args:
            source_id (str): Identifier of the panel being dragged.
            target_id (str): Identifier of the panel being hovered over.
            zone (DropZone): The drop zone relative to the target tile.
        """

        new_orientation: Qt.Orientation
        new_splitter: FlexSplitter
        target_index: int

        source_tile: Optional[PanelTile] = self._find_tile(source_id)
        target_tile: Optional[PanelTile] = self._find_tile(target_id)

        if source_tile is None or target_tile is None:
            return

        source_parent: Optional[FlexSplitter] = self.__find_parent(source_tile)
        target_parent: Optional[FlexSplitter] = self.__find_parent(target_tile)

        # Determine whether the zones align with the target's parent
        # orientation.
        horizontal_zones: set[DropZone] = {DropZone.Left, DropZone.Right}
        vertical_zones: set[DropZone] = {DropZone.Top, DropZone.Bottom}

        # Detach source from its current location.
        source_tile.setParent(None)

        # Clean up the source's old parent if it now has fewer than two
        # children.  We do this before the insertion so that widget indices
        # remain valid.
        if source_parent is not None:
            self.__collapse_if_single(source_parent)

        # After possible collapse the target_parent reference might have
        # changed; re-resolve it.
        target_parent = self.__find_parent(target_tile)

        if target_parent is None:
            # target_tile is currently the root node; we must create a
            # new top-level splitter.
            new_orientation = (
                Qt.Orientation.Horizontal
                if zone in horizontal_zones
                else Qt.Orientation.Vertical
            )
            new_splitter = FlexSplitter(new_orientation, self)

            # _set_root must be called BEFORE addWidget so that the
            # old root (which may be target_tile) is still in the layout
            # when replaceWidget searches for it.
            self._set_root(new_splitter)

            if zone in {DropZone.Left, DropZone.Top}:
                new_splitter.addWidget(source_tile)
                new_splitter.addWidget(target_tile)
            else:
                new_splitter.addWidget(target_tile)
                new_splitter.addWidget(source_tile)

            return

        parent_is_horizontal: bool = (
            target_parent.orientation() == Qt.Orientation.Horizontal
        )
        zone_matches_orientation: bool = (
            zone in horizontal_zones and parent_is_horizontal
        ) or (zone in vertical_zones and not parent_is_horizontal)

        if zone_matches_orientation:
            # Insert source adjacent to target in the existing splitter.
            target_index = target_parent.childIndex(target_tile)
            if zone in {DropZone.Left, DropZone.Top}:
                target_parent.insertWidget(target_index, source_tile)
            else:
                target_parent.insertWidget(target_index + 1, source_tile)
        else:
            # Create a new perpendicular splitter around the target.
            new_orientation = (
                Qt.Orientation.Horizontal
                if zone in horizontal_zones
                else Qt.Orientation.Vertical
            )
            new_splitter = FlexSplitter(new_orientation, self)
            target_index = target_parent.childIndex(target_tile)

            if zone in {DropZone.Left, DropZone.Top}:
                new_splitter.addWidget(source_tile)
                new_splitter.addWidget(target_tile)
            else:
                new_splitter.addWidget(target_tile)
                new_splitter.addWidget(source_tile)

            target_parent.insertWidget(target_index, new_splitter)

    def __collapse_if_single(self, splitter: FlexSplitter) -> None:
        """
        If a splitter has exactly one child remaining, replaces the splitter with that
        child in the widget tree.

        Args:
            splitter (FlexSplitter): The splitter to inspect.
        """

        children: list[FlexChild] = splitter.getFlexChildren()
        if len(children) != 1:
            return

        sole_child: FlexChild = children[0]
        sole_child.setParent(None)

        if splitter is self.__root:
            self._set_root(sole_child)
        else:
            grandparent: Optional[FlexSplitter] = self.__find_parent_splitter(splitter)
            if grandparent is not None:
                idx: int = grandparent.childIndex(splitter)
                splitter.setParent(None)
                grandparent.insertWidget(idx, sole_child)
            else:
                # Fallback - promote to root if no grandparent is found.
                self._set_root(sole_child)

    def __find_parent_splitter(self, target: FlexSplitter) -> Optional[FlexSplitter]:
        """
        Finds the direct `FlexSplitter` parent of `target`.

        Args:
            target (FlexSplitter): The splitter whose parent is sought.

        Returns:
            Optional[FlexSplitter]:
                The parent splitter or `None` if `target` is the root.
        """

        if self.__root is target:
            return None

        return self.__dfs_find_parent_splitter(self.__root, target)

    def __dfs_find_parent_splitter(
        self, node: RootNode, target: FlexSplitter
    ) -> Optional[FlexSplitter]:
        """
        Recursive helper for `__find_parent_splitter()`.

        Args:
            node (RootNode): Current node.
            target (FlexSplitter): The splitter whose parent is sought.

        Returns:
            Optional[FlexSplitter]: Parent splitter or `None`.
        """

        if isinstance(node, PanelTile):
            return None

        for child in node.getFlexChildren():
            if child is target:
                return node

            if isinstance(child, FlexSplitter):
                result: Optional[FlexSplitter] = self.__dfs_find_parent_splitter(
                    child, target
                )
                if result is not None:
                    return result

        return None

    def getLayout(self) -> LayoutNode:
        """
        Serializes the current widget arrangement into a `LayoutNode` model.

        The returned model can be stored as JSON and passed back to `loadLayout()` to
        reconstruct the same arrangement.

        Returns:
            LayoutNode: The root node of the serialized layout tree.
        """

        return self.__node_to_model(self.__root)

    def __node_to_model(self, node: RootNode) -> LayoutNode:
        """
        Recursively converts a widget-tree node into a `LayoutNode`.

        Args:
            node (RootNode): The node to convert.

        Returns:
            LayoutNode: The corresponding model.
        """

        if isinstance(node, PanelTile):
            return PanelNode(identifier=node.content_identifier)

        orientation: str = (
            "horizontal"
            if node.orientation() == Qt.Orientation.Horizontal
            else "vertical"
        )

        children: list[LayoutNode] = [
            self.__node_to_model(child) for child in node.getFlexChildren()
        ]

        return SplitterNode(
            orientation=orientation, children=children, sizes=node.sizes()
        )

    def loadLayout(self, layout: LayoutNode, panels: Mapping[str, FlexContent]) -> None:
        """
        Rebuilds the widget tree from a previously serialized `LayoutNode`.

        `panels` must contain an entry for every `identifier` that appears in the layout
        tree. Panels not referenced by the layout are ignored.

        Args:
            layout (LayoutNode):
                The root node of the serialized layout tree, as returned by
                `getLayout()`.
            panels (Mapping[str, FlexContent]):
                Dictionary mapping panel identifiers to content widgets.

        Raises:
            KeyError:
                If the layout references an identifier that is not present in `panels`.
        """

        new_root: RootNode = self.__model_to_node(layout, panels)
        self._set_root(new_root)

    def __model_to_node(
        self, model: LayoutNode, panels: Mapping[str, FlexContent]
    ) -> RootNode:
        """
        Recursively converts a `LayoutNode` back into a widget-tree node.

        Args:
            model (LayoutNode): The model node to convert.
            panels (Mapping[str, FlexContent]):
                Dictionary mapping identifiers to content widgets.

        Raises:
            KeyError: If a panel identifier is missing from `panels`.

        Returns:
            RootNode: The reconstructed widget-tree node.
        """

        if isinstance(model, PanelNode):
            panel: FlexContent = panels[model.identifier]
            return self.__create_tile(panel)

        qt_orientation: Qt.Orientation = (
            Qt.Orientation.Horizontal
            if model.orientation == "horizontal"
            else Qt.Orientation.Vertical
        )
        splitter = FlexSplitter(qt_orientation, self)

        for child_model in model.children:
            child_widget: RootNode = self.__model_to_node(child_model, panels)
            splitter.addWidget(child_widget)

        if model.sizes and len(model.sizes) == splitter.count():
            splitter.setSizes(model.sizes)

        return splitter

    def setPanelVisible(self, identifier: str, visible: bool) -> None:
        """
        Sets the visibility of the panel with the given identifier.

        Args:
            identifier (str): The identifier of the panel to show or hide.
            visible (bool): Whether the panel should be visible.
        """

        tile: Optional[PanelTile] = self._find_tile(identifier)
        if tile is not None:
            tile.setVisible(visible)
