"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from enum import Enum, auto


class DropZone(Enum):
    """
    The zone within a panel tile over which a dragged tile is currently hovering.
    """

    Left = auto()
    """Left edge - insert before the target in a horizontal splitter."""

    Right = auto()
    """Right edge - insert after the target in a horizontal splitter."""

    Top = auto()
    """Top edge - insert before the target in a vertical splitter."""

    Bottom = auto()
    """Bottom edge - insert after the target in a vertical splitter."""

    Center = auto()
    """Central area - reserved; no reordering is performed when dropping in this zone."""

    @staticmethod
    def from_pos(
        x: int, y: int, width: int, height: int, edge_threshold: float = 0.3
    ) -> DropZone:
        """
        Classifies the given position relative to a widget's bounding box into one of the
        five `DropZone` values.

        The outer edge threshold fraction on each side maps to the corresponding
        directional zone; the rest maps to `DropZone.Center`. A value of 0.30 means the
        outer 30 % on each side map to Left / Right / Top / Bottom; the remaining central
        40 % maps to Center.

        Args:
            x (int): Cursor x-coordinate in widget-local space.
            y (int): Cursor y-coordinate in widget-local space.
            width (int): Widget width in pixels.
            height (int): Widget height in pixels.
            edge_threshold (float, optional):
                Optional override for the edge threshold fraction. Defaults to 0.3.

        Returns:
            DropZone: The zone that best matches the given position.
        """

        left_bound = int(width * edge_threshold)
        right_bound = int(width * (1.0 - edge_threshold))
        top_bound = int(height * edge_threshold)
        bottom_bound = int(height * (1.0 - edge_threshold))

        if x < left_bound:
            return DropZone.Left
        if x >= right_bound:
            return DropZone.Right
        if y < top_bound:
            return DropZone.Top
        if y >= bottom_bound:
            return DropZone.Bottom
        return DropZone.Center
