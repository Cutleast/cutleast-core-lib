"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QSplitter, QWidget

from .panel_tile import PanelTile

type FlexChild = PanelTile | FlexSplitter
"""
Type alias for the two possible child types of an `InternalSplitter`.
"""


class FlexSplitter(QSplitter):
    """
    Splitter widget used by `FlexContainer` to build the widget tree.
    """

    def getFlexChildren(self) -> list[FlexChild]:
        """
        Returns the ordered list of flex children currently inside this splitter.

        Returns:
            list[FlexChild]: Ordered list of flex children.
        """

        result: list[FlexChild] = []
        for index in range(self.count()):
            child: Optional[QWidget] = self.widget(index)
            if isinstance(child, (PanelTile, FlexSplitter)):
                result.append(child)

        return result

    def childIndex(self, child: FlexChild) -> int:
        """
        Returns the index of the given child in this splitter.

        Args:
            child (FlexChild): The child to find the index of.

        Raises:
            ValueError: If the child is not found in this splitter.

        Returns:
            int: The index of the child.
        """

        return self.getFlexChildren().index(child)
