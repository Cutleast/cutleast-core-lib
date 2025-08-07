"""
Copyright (c) Cutleast
"""

import webbrowser

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton


class LinkButton(QPushButton):
    """
    Custom QPushButton adapted for hyperlinks.
    """

    def __init__(
        self, url: str, display_text: str | None = None, icon: QIcon | None = None
    ) -> None:
        """
        Args:
            url (str): URL that is opened when the button is clicked.
            display_text (str | None, optional): Text to display. Defaults to None.
            icon (QIcon | None, optional): Icon to display. Defaults to None.
        """

        super().__init__()

        if display_text is not None:
            self.setText(display_text)

        if icon is not None:
            self.setIcon(icon)

        self.clicked.connect(lambda: webbrowser.open(url))
        self.setToolTip(url)
