"""
Copyright (c) Cutleast
"""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton

from ..utilities.icon_provider import IconProvider


class KeyLineEdit(QLineEdit):
    """
    Custom QLineEdit specialized for sensitive input like passwords or keys.
    This field hides the text by default and has a button to show it.
    """

    __visibility_button: QPushButton

    __visible_icon: QIcon
    __hidden_icon: QIcon

    def __init__(self, *args: Any, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)

        self.__visible_icon = IconProvider.get_qta_icon("mdi6.eye-off")
        self.__hidden_icon = IconProvider.get_qta_icon("mdi6.eye")

        self.__init_ui()

        self.textChanged.connect(
            lambda t: self.__visibility_button.setVisible(bool(t.strip()))
        )
        self.__visibility_button.clicked.connect(self.__toggle_visibility)

        self.__visibility_button.setChecked(False)
        self.__toggle_visibility()

    def __init_ui(self) -> None:
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hlayout)

        # Push button to the right-hand side
        hlayout.addStretch()

        self.__visibility_button = QPushButton()
        self.__visibility_button.setToolTip(self.tr("Toggle password visibility"))
        self.__visibility_button.setObjectName("toggle_button")
        self.__visibility_button.setCursor(Qt.CursorShape.ArrowCursor)
        self.__visibility_button.setCheckable(True)
        self.__visibility_button.setVisible(bool(self.text().strip()))
        hlayout.addWidget(self.__visibility_button)

    def __toggle_visibility(self) -> None:
        if self.__visibility_button.isChecked():
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            self.__visibility_button.setIcon(self.__visible_icon)
        else:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self.__visibility_button.setIcon(self.__hidden_icon)
