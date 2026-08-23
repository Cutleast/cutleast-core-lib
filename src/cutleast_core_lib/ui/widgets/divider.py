"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QSizePolicy


class Divider(QFrame):
    """
    A horizontal or vertical line used to separate content in the UI.
    """

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal) -> None:
        """
        Args:
            orientation (Qt.Orientation): Orientation of the divider.
        """

        super().__init__()

        self.setProperty(
            "orientation",
            "horizontal" if orientation == Qt.Orientation.Horizontal else "vertical",
        )

        if orientation == Qt.Orientation.Horizontal:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
