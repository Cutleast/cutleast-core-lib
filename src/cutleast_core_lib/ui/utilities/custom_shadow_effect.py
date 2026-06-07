"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import QObject
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsDropShadowEffect


class CustomShadowEffect(QGraphicsDropShadowEffect):
    """
    Custom shadow effect that can be applied to widgets.
    """

    __strength: int

    @override
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.__strength = 1

    def setStrength(self, strength: int, /) -> None:
        """
        Sets the strength of the shadow effect.

        Args:
            strength (int): The strength of the shadow effect.
        """

        self.__strength = strength

    @override
    def draw(self, painter: QPainter) -> None:
        for _ in range(self.__strength):
            super().draw(painter)
