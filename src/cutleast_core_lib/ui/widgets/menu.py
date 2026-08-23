"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction, QCursor, QIcon, QPixmap, QShowEvent, Qt
from PySide6.QtWidgets import QMenu, QWidget

from ..theme.manager import ThemeManager
from ..theme.models.theme import Theme
from ..utilities import apply_shadow


class Menu(QMenu):
    """
    Adapted QMenu with a custom drop shadow.
    """

    __shadow_margin: int
    __shadow_size: int

    @override
    def __init__(
        self,
        icon: Optional[QIcon | QPixmap] = None,
        title: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        if title is not None:
            super().__init__(title, parent)
        else:
            super().__init__(parent)

        if icon is not None:
            self.setIcon(icon)

        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.__update_shadow(ThemeManager.get().theme)
        ThemeManager.get().theme_changed.connect(self.__on_theme_changed)

    def __update_shadow(self, theme: Theme) -> None:
        """
        Updates the menu shadow and its reserved margin from the current theme.

        Args:
            theme (Theme): The theme supplying the shadow metrics and color.
        """

        self.__shadow_margin = theme.metrics.shadow_margin
        self.__shadow_size = theme.metrics.shadow_size
        self.setStyleSheet(f"Menu {{ margin: {self.__shadow_margin}px; }}")
        apply_shadow(
            widget=self,
            size=self.__shadow_size,
            shadow_color=theme.resolve(theme.colors.shadow),
        )

    def __on_theme_changed(self, theme: Theme) -> None:
        """
        Updates the shadow after the application theme changes.
        """

        self.__update_shadow(theme)

    @override
    def showEvent(self, event: QShowEvent) -> None:
        """
        Positions the shadow frame without moving the visible menu panel.

        Args:
            event (QShowEvent): The event emitted when the menu is shown.
        """

        super().showEvent(event)

        if self.__opens_upward():
            self.__adjust_upward_menu_position()
            return

        parent_menu: Optional[QMenu] = self.__get_parent_menu()
        if parent_menu is None:
            self.__adjust_root_menu_position()
            return

        self.__adjust_submenu_position()

    def __get_parent_menu(self) -> Optional[QMenu]:
        """
        Gets the menu that contains this menu as a submenu.

        Returns:
            Optional[QMenu]: The containing menu, or `None` for a root menu.
        """

        for widget in self.menuAction().associatedObjects():
            if isinstance(widget, QMenu):
                return widget

        return None

    def __adjust_root_menu_position(self) -> None:
        """
        Adjusts a root menu while keeping its visible panel at Qt's anchor.
        """

        position: QPoint = self.pos()
        self.move(position - QPoint(self.__shadow_margin, self.__shadow_margin))

    def __adjust_submenu_position(self) -> None:
        """
        Adjusts a submenu while keeping its visible panel at Qt's anchor.
        """

        position: QPoint = self.pos()
        visible_actions: list[QAction] = [
            action
            for action in self.actions()
            if action.isVisible() and not action.isSeparator()
        ]
        vertical_offset: int = self.__shadow_margin if len(visible_actions) == 1 else 0
        self.move(position - QPoint(self.__shadow_margin, vertical_offset))

    def __adjust_upward_menu_position(self) -> None:
        """
        Adjusts a menu that Qt positioned above the cursor.
        """

        position: QPoint = self.pos()
        self.move(position - QPoint(self.__shadow_margin, -self.__shadow_margin))

    def __opens_upward(self) -> bool:
        """
        Gets whether Qt positioned the menu entirely above the cursor.

        Returns:
            bool: `True` when the menu was opened upwards.
        """

        cursor_position: QPoint = QCursor.pos()
        menu_geometry = self.frameGeometry()
        return (
            menu_geometry.top() < cursor_position.y()
            and menu_geometry.bottom() <= cursor_position.y()
        )
