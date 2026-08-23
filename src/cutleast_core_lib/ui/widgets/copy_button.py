"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtCore import Qt, QTimerEvent, Signal

from ..utilities.icon_provider import IconProvider
from .icon_button import IconButton


class CopyButton(IconButton):
    """
    Custom QPushButton which shows a copy icon and changes it to a check mark icon for
    three seconds upon click.
    """

    copyClicked = Signal()
    """
    Signal emitted when the button is clicked. Use this instead of `clicked` to avoid
    conflict with the icon timer.
    """

    __icon: IconProvider.ThemeIconBinding

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__icon = IconProvider.bind_qta_icon(self, self.setIcon, "mdi6.content-copy")

        self.clicked.connect(self.__on_click)

    @override
    def timerEvent(self, e: QTimerEvent) -> None:
        super().timerEvent(e)

        self.__icon.refresh()  # this reverts the icon

    def __on_click(self) -> None:
        # overriding the icon this way has the (minor) drawback that a theme change
        # during the 3 seconds will revert the icon too early
        self.setIcon(IconProvider.get_qta_icon("mdi6.check-bold"))
        self.startTimer(3000, timerType=Qt.TimerType.PreciseTimer)

        self.copyClicked.emit()
