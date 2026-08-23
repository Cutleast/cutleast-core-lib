"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton, QSizePolicy


class IconButton(QPushButton):
    """
    Custom QPushButton which is designed to be used as an icon-only button.
    """

    def __init__(self, icon: Optional[QIcon] = None) -> None:
        """
        Args:
            icon (Optional[QIcon], optional):
                The initial icon to display on the button. Defaults to None.
        """

        super().__init__("")

        if icon is not None:
            self.setIcon(icon)

        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
