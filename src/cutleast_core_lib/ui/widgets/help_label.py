"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtCore import QEvent
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QLabel

from ..theme.manager import ThemeManager
from ..utilities.icon_provider import IconProvider


class HelpLabel(QLabel):
    """
    A label that displays help text when hovered over.
    """

    @override
    def __init__(self, help_text: str) -> None:
        super().__init__(help_text)

        self.setToolTip(help_text)

        # TODO: Use an icon binding that updates the icon when the theme changes
        self.setPixmap(
            IconProvider.get_qta_icon("mdi6.information").pixmap(
                ThemeManager.get().theme.metrics.icon_l,
                ThemeManager.get().theme.metrics.icon_l,
            )
        )

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        super().enterEvent(event)

        self.setPixmap(
            IconProvider.get_qta_icon(
                "mdi6.information", color=self.palette().accent().color().name()
            ).pixmap(
                ThemeManager.get().theme.metrics.icon_l,
                ThemeManager.get().theme.metrics.icon_l,
            )
        )

    @override
    def leaveEvent(self, event: QEvent) -> None:
        super().leaveEvent(event)

        self.setPixmap(
            IconProvider.get_qta_icon("mdi6.information").pixmap(
                ThemeManager.get().theme.metrics.icon_l,
                ThemeManager.get().theme.metrics.icon_l,
            )
        )
