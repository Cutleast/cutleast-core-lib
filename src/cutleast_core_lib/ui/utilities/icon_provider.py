"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtGui import QIcon, QPalette


class IconProvider:
    """
    Class for providing icons.
    """

    @classmethod
    def get_qta_icon_for_palette(cls, icon_name: str, palette: QPalette) -> QIcon:
        """
        Gets the specified icon from qtawesome and returns it with the correct colors.

        Args:
            icon_name (str): The name of the icon to get.
            palette (QPalette): The palette to use for the icon.

        Returns:
            QIcon: The icon with the correct colors.
        """

        return IconProvider.get_qta_icon(icon_name, palette.text().color().name())

    @classmethod
    def get_qta_icon(
        cls, icon_name: str, color: str, disabled_color: str = "#666666"
    ) -> QIcon:
        """
        Gets the specified icon from qtawesome and returns it with the correct colors.

        Args:
            icon_name (str): The name of the icon to get.
            color (str): The color to use for the icon.
            disabled_color (str, optional):
                The color to use for the disabled icon. Defaults to "#666666".

        Returns:
            QIcon: The icon with the correct colors.
        """

        return qta.icon(icon_name, color=color, color_disabled=disabled_color)

    @classmethod
    def get_icon_name_for_palette(cls, icon_name: str, palette: QPalette) -> str:
        """
        Returns the icon name for the text color of the specified palette.

        Args:
            icon_name (str): Base name of the icon
            palette (QPalette): Palette

        Raises:
            ValueError:
                when text color of the specified palette is neither #000000 nor #FFFFFF

        Returns:
            str: Full icon name with file suffix
        """

        text_color: str = palette.text().color().name().upper()

        match text_color:
            case "#000000":
                return f"{icon_name}_dark.svg"
            case "#FFFFFF":
                return f"{icon_name}_light.svg"
            case _:
                raise ValueError(f"Unknown text color: {text_color}")

    @classmethod
    def get_icon_for_palette(cls, icon_name: str, palette: QPalette) -> QIcon:
        """
        Provides an icon for the text color of the specified palette.

        Args:
            icon_name (str): Base name of the icon
            palette (QPalette): Palette

        Raises:
            ValueError:
                when text color of the specified palette is neither #000000 nor #FFFFFF

        Returns:
            QIcon: Icon
        """

        full_icon_name: str = ":/icons/" + IconProvider.get_icon_name_for_palette(
            icon_name, palette
        )
        return QIcon(full_icon_name)
