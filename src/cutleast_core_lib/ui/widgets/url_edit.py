"""
Copyright (c) Cutleast
"""

import webbrowser
from typing import Any, Optional, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton

from ..utilities.icon_provider import IconProvider
from .icon_button import IconButton


class UrlEdit(QLineEdit):
    """
    LineEdit with open url button.
    """

    __open_url_button: QPushButton

    @override
    def __init__(self, *args: Any, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hlayout)

        hlayout.addStretch()

        self.__open_url_button = IconButton()
        IconProvider.bind_qta_icon(
            self.__open_url_button, self.__open_url_button.setIcon, "mdi6.open-in-new"
        )
        self.__open_url_button.setToolTip(self.tr("Open URL in default browser..."))
        self.__open_url_button.clicked.connect(self.__open_url)
        self.__open_url_button.setCursor(Qt.CursorShape.ArrowCursor)
        self.__open_url_button.setEnabled(bool(self.text().strip()))
        hlayout.addWidget(self.__open_url_button)

        self.textChanged.connect(self.__on_text_change)

    def __on_text_change(self, text: str) -> None:
        self.__open_url_button.setEnabled(bool(text.strip()))

    def __open_url(self) -> None:
        url: Optional[str] = self.text().strip() if self.text().strip() else None

        if url is not None:
            webbrowser.open(url)
