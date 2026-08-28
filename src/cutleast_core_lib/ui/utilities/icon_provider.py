"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import TypeVar

import qtawesome as qta
import shiboken6
from PySide6.QtCore import QFile, QObject, Signal
from PySide6.QtGui import QIcon, QPainter, QPixmap

from cutleast_core_lib.core.utilities.singleton import SingletonQObject
from cutleast_core_lib.ui.theme.models.theme import Theme
from cutleast_core_lib.ui.theme.models.types import ThemeAlias

T = TypeVar("T", bound="IconProvider")


class IconProvider(SingletonQObject):
    """
    Singleton class for providing icons.
    """

    class Color(StrEnum):
        """Enum for pre-defined icon colors."""

        Title = "${texts.title.color}"
        """Corresponds to the title color of the current theme."""

        Subtitle = "${texts.subtitle.color}"
        """Corresponds to the subtitle color of the current theme."""

        Text = "${texts.text.color}"
        """Corresponds to the text color of the current theme."""

        Secondary = "${texts.secondary.color}"
        """Corresponds to the secondary text color of the current theme."""

        Primary = "${colors.primary_fg}"
        """Corresponds to the primary color of the current theme."""

        Destructive = "${colors.error_fg}"
        """Corresponds to the destructive color of the current theme."""

        Error = "${colors.error_fg}"
        """Corresponds to the error color of the current theme."""

        Caution = "${colors.caution_fg}"
        """Corresponds to the caution color of the current theme."""

        Warning = "${colors.warning_fg}"
        """Corresponds to the warning color of the current theme."""

        Success = "${colors.success_fg}"
        """Corresponds to the warning color of the current theme."""

        Information = "${colors.information_fg}"
        """Corresponds to the information color of the current theme."""

    class ThemeIconBinding(QObject):
        """
        Keeps one icon target synchronized with the current IconProvider theme.
        """

        __target: QObject
        __consumer: Callable[[QIcon], None]
        __factory: Callable[[], QIcon]

        def __init__(
            self,
            target: QObject,
            consumer: Callable[[QIcon], None],
            factory: Callable[[], QIcon],
        ) -> None:
            """
            Args:
                target (QObject): Icon-owning target, such as a QAction.
                consumer (Callable[[QIcon], None]): Applies the recreated icon.
                factory (Callable[[], QIcon]): Creates the themed icon.
            """

            super().__init__(target)

            self.__target = target
            self.__consumer = consumer
            self.__factory = factory

            IconProvider.get()._refresh_required.connect(self.refresh)

            self.refresh()

        def refresh(self) -> None:
            """
            Recreates and applies the icon for the active theme.
            """

            if not shiboken6.isValid(self.__target):
                # target has been deleted, so we can disconnect the signal and stop
                # updating the icon
                try:
                    IconProvider.get()._refresh_required.disconnect(self.refresh)
                except RuntimeError:
                    # signal was not connected, so we can ignore this error
                    pass

                return

            self.__consumer(self.__factory())

        def replace(
            self, consumer: Callable[[QIcon], None], factory: Callable[[], QIcon]
        ) -> None:
            """
            Replaces the icon configuration and refreshes the target.

            Args:
                consumer (Callable[[QIcon], None]): Applies the recreated icon.
                factory (Callable[[], QIcon]): Creates the current themed icon.
            """

            self.__consumer = consumer
            self.__factory = factory
            self.refresh()

    _refresh_required = Signal()
    """Signal emitted when the theme changes and icons need to be refreshed."""

    __theme: Theme

    def __init__(self, theme: Theme) -> None:
        """
        Args:
            theme (Theme): The theme to use for the icons.

        Raises:
            RuntimeError: When the class is already initialized.
        """

        super().__init__()

        self.set_theme(theme)

    def set_theme(self, theme: Theme) -> None:
        """
        Sets the theme to use for the icons.

        Args:
            theme (Theme): The theme to use for the icons.
        """

        self.__theme = theme
        self._refresh_required.emit()

    @classmethod
    def bind_custom_icon(
        cls,
        target: QObject,
        consumer: Callable[[QIcon], None],
        factory: Callable[[], QIcon],
    ) -> ThemeIconBinding:
        """
        Binds a icon from a specified factory to be applied via a consumer each time,
        the current theme changes.

        Replaces any existing binding for the same parent with the new consumer and
        factory.

        Args:
            target (QObject): The target QObject.
            consumer (Callable[[QIcon], None]): A function that consumes the icon.
            factory (Callable[[], QIcon]): A function that creates the icon.

        Returns:
            ThemeIconBinding:
                The binding object that keeps the icon updated with the current theme.
        """

        for child in target.children():
            if isinstance(child, cls.ThemeIconBinding):
                child.replace(consumer, factory)
                return child

        return cls.ThemeIconBinding(target, consumer, factory)

    @classmethod
    def get_qta_icon(
        cls,
        icon_name: str,
        /,
        *,
        color: ThemeAlias = Color.Text,
        color_disabled: ThemeAlias = Color.Secondary,
        color_active: ThemeAlias = Color.Text,
        color_selected: ThemeAlias = Color.Primary,
        color_on: ThemeAlias = Color.Primary,
        scale_factor: float = 1.0,
    ) -> QIcon:
        """
        Gets the specified icon from qtawesome and returns it with the correct colors.

        Args:
            icon_name (str): The name of the icon to get.
            color (ThemeAlias, optional): The color of the icon. Defaults to Color.Text.
            color_disabled (ThemeAlias, optional):
                The color of the icon when disabled. Defaults to Color.Secondary.
            color_active (ThemeAlias, optional):
                The color of the icon when active. Defaults to Color.Text.
            color_selected (ThemeAlias, optional):
                The color of the icon when selected. Defaults to Color.Primary.
            color_on (ThemeAlias, optional):
                The color of the icon when on (e.g. current tab). Defaults to
                Color.Primary.
            scale_factor (float, optional):
                The scale factor to apply to the icon. Defaults to 1.0.

        Raises:
            RuntimeError: When the class is not initialized.

        Returns:
            QIcon: The icon with the correct colors.
        """

        theme: Theme = cls.get().__theme

        return qta.icon(
            icon_name,
            color=theme.resolve(color),
            color_disabled=theme.resolve(color_disabled),
            color_active=theme.resolve(color_active),
            color_selected=theme.resolve(color_selected),
            color_on=theme.resolve(color_on),
            scale_factor=scale_factor,
        )

    @classmethod
    def bind_qta_icon(
        cls,
        target: QObject,
        consumer: Callable[[QIcon], None],
        icon_name: str,
        /,
        *,
        color: ThemeAlias = Color.Text,
        color_disabled: ThemeAlias = Color.Secondary,
        color_active: ThemeAlias = Color.Text,
        color_selected: ThemeAlias = Color.Primary,
        color_on: ThemeAlias = Color.Primary,
        scale_factor: float = 1.0,
    ) -> ThemeIconBinding:
        """
        Binds the specified icon from qtawesome to the specified consumer and keeps it
        updated with the current theme.

        Usage:
            ```
            IconProvider.bind_qta_icon(
                self.my_button,
                self.my_button.setIcon,
                "fa5s.home",
                color=IconProvider.Color.Primary,
            )
            ```

        Args:
            target (QObject): The target QObject.
            consumer (Callable[[QIcon], None]): A function that consumes the icon.
            icon_name (str): The name of the icon to get.
            color (ThemeAlias, optional): The color of the icon. Defaults to Color.Text.
            color_disabled (ThemeAlias, optional):
                The color of the icon when disabled. Defaults to Color.Secondary.
            color_active (ThemeAlias, optional):
                The color of the icon when active. Defaults to Color.Text.
            color_selected (ThemeAlias, optional):
                The color of the icon when selected. Defaults to Color.Primary.
            color_on (ThemeAlias, optional):
                The color of the icon when on (e.g. current tab). Defaults to
                Color.Primary.
            scale_factor (float, optional):
                The scale factor to apply to the icon. Defaults to 1.0.

        Raises:
            RuntimeError: When the class is not initialized.

        Returns:
            ThemeIconBinding:
                The binding object that keeps the icon updated with the current theme.
        """

        return cls.bind_custom_icon(
            target,
            consumer,
            lambda: cls.get_qta_icon(
                icon_name,
                color=color,
                color_disabled=color_disabled,
                color_active=color_active,
                color_selected=color_selected,
                color_on=color_on,
                scale_factor=scale_factor,
            ),
        )

    @classmethod
    def get_icon(
        cls,
        icon_name: str,
        /,
        *,
        set_colors: bool = True,
        color: ThemeAlias = Color.Text,
        color_disabled: ThemeAlias = Color.Secondary,
        color_active: ThemeAlias = Color.Text,
        color_selected: ThemeAlias = Color.Primary,
        color_on: ThemeAlias = Color.Primary,
        resource_prefix: str = ":/core-lib/icons",
    ) -> QIcon:
        """
        Provides an icon for the current theme.

        Args:
            icon_name (str): Base name of the icon (without suffix).
            set_colors (bool, optional):
                Whether to set the colors of the icon or return it as-is. Defaults to
                True.
            color (ThemeAlias, optional): The color of the icon. Defaults to Color.Text.
            color_disabled (ThemeAlias, optional):
                The color of the icon when disabled. Defaults to Color.Secondary.
            color_active (ThemeAlias, optional):
                The color of the icon when active. Defaults to Color.Text.
            color_selected (ThemeAlias, optional):
                The color of the icon when selected. Defaults to Color.Primary.
            color_on (ThemeAlias, optional):
                The color of the icon when on (e.g. current tab). Defaults to
                Color.Primary.
            resource_prefix (str, optional): The resource directory containing the
                icon files. Defaults to :/core-lib/icons.

        Raises:
            RuntimeError: When the class is not initialized.
            FileNotFoundError: When the icon is not found.

        Returns:
            QIcon: Icon.
        """

        suffixes: list[str] = [".svg", ".png", ".jpg", ".jpeg", ".ico", ".gif"]

        for suffix in suffixes:
            icon_file: str = f"{resource_prefix}/{icon_name}{suffix}"

            if not QFile.exists(icon_file):
                continue

            if not set_colors:
                return QIcon(icon_file)

            icon = QIcon()

            pixmap = QPixmap(icon_file)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), cls.get().__theme.resolve(color))
            painter.end()
            icon.addPixmap(pixmap, QIcon.Mode.Normal)

            pixmap = QPixmap(icon_file)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), cls.get().__theme.resolve(color_disabled))
            painter.end()
            icon.addPixmap(pixmap, QIcon.Mode.Disabled)

            pixmap = QPixmap(icon_file)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), cls.get().__theme.resolve(color_active))
            painter.end()
            icon.addPixmap(pixmap, QIcon.Mode.Active)

            pixmap = QPixmap(icon_file)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), cls.get().__theme.resolve(color_selected))
            painter.end()
            icon.addPixmap(pixmap, QIcon.Mode.Selected)

            pixmap = QPixmap(icon_file)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), cls.get().__theme.resolve(color_on))
            painter.end()
            icon.addPixmap(pixmap, QIcon.Mode.Normal, QIcon.State.On)

            return icon

        raise FileNotFoundError(
            f"Could not find icon {icon_name} for mode {cls.get().__theme.ui_mode.name}!"
        )

    @classmethod
    def bind_icon(
        cls,
        target: QObject,
        consumer: Callable[[QIcon], None],
        icon_name: str,
        /,
        *,
        set_colors: bool = True,
        color: ThemeAlias = Color.Text,
        color_disabled: ThemeAlias = Color.Secondary,
        color_active: ThemeAlias = Color.Text,
        color_selected: ThemeAlias = Color.Primary,
        color_on: ThemeAlias = Color.Primary,
        resource_prefix: str = ":/core-lib/icons",
    ) -> ThemeIconBinding:
        """
        Binds the specified icon to the specified consumer and keeps it updated with the
        current theme.

        Usage:
            ```
            IconProvider.bind_icon(
                self.my_button,
                self.my_button.setIcon,
                "my_icon",
                color=IconProvider.Color.Primary,
            )
            ```

        Args:
            target (QObject): The target QObject.
            consumer (Callable[[QIcon], None]): A function that consumes the icon.
            icon_name (str): The name of the icon to get.
            set_colors (bool, optional):
                Whether to set the colors of the icon or return it as-is. Defaults to
            color (ThemeAlias, optional): The color of the icon. Defaults to Color.Text.
            color_disabled (ThemeAlias, optional):
                The color of the icon when disabled. Defaults to Color.Secondary.
            color_active (ThemeAlias, optional):
                The color of the icon when active. Defaults to Color.Text.
            color_selected (ThemeAlias, optional):
                The color of the icon when selected. Defaults to Color.Primary.
            color_on (ThemeAlias, optional):
                The color of the icon when on (e.g. current tab). Defaults to
                Color.Primary.
            resource_prefix (str, optional): The resource directory containing the
                icon files. Defaults to :/core-lib/icons.

        Raises:
            RuntimeError: When the class is not initialized.
            FileNotFoundError: When the icon is not found.

        Returns:
            ThemeIconBinding:
                The binding object that keeps the icon updated with the current theme.
        """

        return cls.bind_custom_icon(
            target,
            consumer,
            lambda: cls.get_icon(
                icon_name,
                set_colors=set_colors,
                color=color,
                color_disabled=color_disabled,
                color_active=color_active,
                color_selected=color_selected,
                color_on=color_on,
                resource_prefix=resource_prefix,
            ),
        )
