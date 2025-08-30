"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from typing import Optional, TypeVar

import qtawesome as qta
from PySide6.QtCore import QFile
from PySide6.QtGui import QIcon

from cutleast_core_lib.core.utilities.singleton import Singleton
from cutleast_core_lib.ui.utilities.ui_mode import UIMode

T = TypeVar("T", bound="IconProvider")


class IconProvider(Singleton):
    """
    Singleton class for providing icons.
    """

    __ui_mode: UIMode
    __icon_color: str

    def __init__(self, ui_mode: UIMode, icon_color: str) -> None:
        """
        Args:
            ui_mode (UIMode): The current UI mode.
            icon_color (str): The color to use for the icons.

        Raises:
            RuntimeError: When the class is already initialized.
        """

        super().__init__(replace_existing_instance=True)

        self.__ui_mode = ui_mode
        self.__icon_color = icon_color

    @classmethod
    def get_qta_icon(
        cls,
        icon_name: str,
        *,
        color: Optional[str] = None,
        disabled_color: str = "#666666",
    ) -> QIcon:
        """
        Gets the specified icon from qtawesome and returns it with the correct colors.

        Args:
            icon_name (str): The name of the icon to get.
            color (Optional[str], optional):
                The color to use for the icon. Defaults to None.
            disabled_color (str, optional):
                The color to use for the disabled icon. Defaults to "#666666".

        Raises:
            RuntimeError: When the class is not initialized.

        Returns:
            QIcon: The icon with the correct colors.
        """

        if color is None:
            color = cls.get().__icon_color

        return qta.icon(icon_name, color=color, color_disabled=disabled_color)

    @classmethod
    def get_icon(cls, icon_name: str) -> QIcon:
        """
        Provides an icon for the current UI mode.

        Args:
            icon_name (str): Base name of the icon (without suffix).

        Raises:
            RuntimeError: When the class is not initialized.
            FileNotFoundError: When the icon is not found.

        Returns:
            QIcon: Icon.
        """

        suffixes: list[str] = [".svg", ".png", ".jpg", ".jpeg", ".ico", ".gif"]

        for suffix in suffixes:
            mode_spec_icon_name: str = (
                ":/icons/" + cls.get().__ui_mode.name.lower() + "/" + icon_name + suffix
            )
            general_icon_name: str = ":/icons/" + icon_name + suffix

            if QFile(mode_spec_icon_name).exists():
                return QIcon(mode_spec_icon_name)
            elif QFile(general_icon_name).exists():
                return QIcon(general_icon_name)

        raise FileNotFoundError(
            f"Could not find icon {icon_name} for mode {cls.get().__ui_mode.name}!"
        )
