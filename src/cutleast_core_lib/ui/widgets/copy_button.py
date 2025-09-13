"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtCore import Qt, QTimerEvent
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton

from cutleast_core_lib.ui.utilities.icon_provider import IconProvider


class CopyButton(QPushButton):
    """
    Custom QPushButton which shows a copy icon and changes it to a check mark icon for
    three seconds upon click.
    """

    __copy_icon: QIcon
    __check_icon: QIcon

    def __init__(self) -> None:
        super().__init__()

        self.__copy_icon = IconProvider.get_qta_icon("mdi6.content-copy")
        self.__check_icon = IconProvider.get_qta_icon("mdi6.check-bold")

        self.setIcon(self.__copy_icon)

        self.clicked.connect(self.__on_click)

    @override
    def timerEvent(self, e: QTimerEvent) -> None:
        super().timerEvent(e)

        self.setIcon(self.__copy_icon)

    def __on_click(self) -> None:
        self.setIcon(self.__check_icon)
        self.startTimer(3000, timerType=Qt.TimerType.PreciseTimer)
