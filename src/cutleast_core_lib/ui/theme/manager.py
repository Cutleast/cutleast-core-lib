"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional, cast, final

from PySide6.QtCore import Signal
from PySide6.QtGui import QFontDatabase, Qt
from PySide6.QtWidgets import QApplication, QWidget

from cutleast_core_lib.core.utilities.singleton import SingletonQObject

from ..utilities.icon_provider import IconProvider
from .generator import ThemeGenerator
from .models.theme import Theme
from .models.types import HexColorStr, ResolvedUiMode
from .renderer import StyleSheetRenderer
from .ui_mode import UiMode


class ThemeManager(SingletonQObject):
    """
    Singleton object for managing the application theme and fonts.
    """

    CORE_RES_QSS_FILES: list[str] = [
        ":/core-lib/styles/base.qss",
        ":/core-lib/styles/common.qss",
        ":/core-lib/styles/area.qss",
        ":/core-lib/styles/buttons.qss",
        ":/core-lib/styles/inputs.qss",
        ":/core-lib/styles/menu.qss",
        ":/core-lib/styles/popup.qss",
        ":/core-lib/styles/progress.qss",
        ":/core-lib/styles/scroll.qss",
        ":/core-lib/styles/splitter.qss",
        ":/core-lib/styles/statusbar.qss",
        ":/core-lib/styles/tab.qss",
        ":/core-lib/styles/toolbar.qss",
        ":/core-lib/styles/view.qss",
    ]
    """The QSS files from the core resources."""

    CORE_BASE_THEME_FILES: list[str] = [":/core-lib/theme/base.json"]
    """The base theme file from the core resources."""

    CORE_DARK_THEME_FILES: list[str] = [":/core-lib/theme/dark.json"]
    """The dark theme file from the core resources."""

    CORE_LIGHT_THEME_FILES: list[str] = [":/core-lib/theme/light.json"]
    """The light theme file from the core resources."""

    CORE_FONT_RESOURCES: list[str] = [
        ":/core-lib/fonts/Inter-VariableFont_opsz,wght.ttf",
        ":/core-lib/fonts/Inter-Italic-VariableFont_opsz,wght.ttf",
        ":/core-lib/fonts/RobotoMono-VariableFont_wght.ttf",
        ":/core-lib/fonts/RobotoMono-Italic-VariableFont_wght.ttf",
    ]
    """The font resources from the core resources."""

    theme_changed = Signal(Theme)
    """
    Signal emitted when the theme changes.

    Args:
        Theme: The new theme.
    """

    __icon_provider: Optional[IconProvider]

    __app: QApplication
    __primary_color: HexColorStr
    __ui_mode: UiMode
    __qss_files: list[str]
    __base_theme_files: list[str]
    __dark_theme_files: list[str]
    __light_theme_files: list[str]

    __cur_theme: Theme
    __cur_stylesheet: str

    log: logging.Logger = logging.getLogger("ThemeManager")

    def __init__(
        self,
        app: QApplication,
        initial_primary_color: HexColorStr,
        initial_ui_mode: UiMode = UiMode.System,
        qss_files: list[str] = CORE_RES_QSS_FILES,
        base_theme_files: list[str] = CORE_BASE_THEME_FILES,
        dark_theme_files: list[str] = CORE_DARK_THEME_FILES,
        light_theme_files: list[str] = CORE_LIGHT_THEME_FILES,
        font_resources: list[str] = CORE_FONT_RESOURCES,
    ) -> None:
        """
        Args:
            app (QApplication): The QApplication instance.
            initial_primary_color (HexColorStr):
                The initial primary accent color for the application.
            initial_ui_mode (UiMode, optional):
                The initial UI mode for the application. Defaults to UiMode.System.
            qss_files (list[str], optional):
                The raw QSS files for the application stylesheet. Defaults to
                CORE_RES_QSS_FILES.
            base_theme_files (list[str], optional):
                The base theme files for both UI modes. Defaults to
                CORE_BASE_THEME_FILES.
            dark_theme_files (list[str], optional):
                The theme files specifically for the dark mode. Defaults to
                CORE_DARK_THEME_FILES.
            light_theme_files (list[str], optional):
                The theme files specifically. Defaults to CORE_LIGHT_THEME_FILES.
            font_resources (list[str], optional):
                A list of font resource files to add to the QFontDatabase. Defaults to
                CORE_FONT_RESOURCES.
        """

        super().__init__(app)

        self.__icon_provider = None
        self.__app = app
        self.__primary_color = initial_primary_color
        self.__ui_mode = initial_ui_mode
        self.__qss_files = qss_files
        self.__base_theme_files = base_theme_files
        self.__dark_theme_files = dark_theme_files
        self.__light_theme_files = light_theme_files

        self.set_ui_mode(initial_ui_mode)

        for font in font_resources:
            ThemeManager.__add_font(font)

    def set_primary_color(self, primary_color: HexColorStr, apply: bool = True) -> None:
        """
        Sets the primary accent color for the application and updates the theme
        accordingly.

        Args:
            primary_color (HexColorStr): The new primary accent color.
            apply (bool, optional):
                Whether to apply the new color immediately. Defaults to True.
        """

        self.__primary_color = primary_color

        if apply:
            self.__set_ui_mode(self.theme.ui_mode)

    def set_ui_mode(self, ui_mode: UiMode) -> None:
        """
        Sets the UI mode for the application and updates the theme accordingly.

        Args:
            ui_mode (UiMode): The new UI mode to set.
        """

        self.__ui_mode = ui_mode

        self.__app.styleHints().setColorScheme(
            # unknown sets to system default
            ui_mode.to_qt_color_scheme()
        )

        resolved_ui_mode: ResolvedUiMode = self.__resolve_ui_mode(ui_mode)
        self.__set_ui_mode(resolved_ui_mode)

        if ui_mode == UiMode.System:
            self.__app.styleHints().colorSchemeChanged.connect(
                self.__on_color_scheme_changed
            )

        else:
            try:
                self.__app.styleHints().colorSchemeChanged.disconnect(
                    self.__on_color_scheme_changed
                )
            except RuntimeError:
                # The signal was not connected, so we can ignore this error.
                pass

    def __set_ui_mode(self, ui_mode: ResolvedUiMode) -> None:
        """
        Sets the UI mode for the application and updates the theme accordingly.

        Args:
            ui_mode (ResolvedUiMode): The new UI mode to set.
        """

        theme_files: list[str] = self.__base_theme_files.copy()
        if ui_mode == UiMode.Dark:
            theme_files.extend(self.__dark_theme_files)
        else:
            theme_files.extend(self.__light_theme_files)

        self.__cur_theme = ThemeGenerator.generate(theme_files, self.__primary_color)
        self.__cur_stylesheet = StyleSheetRenderer.render(
            self.__qss_files, self.__cur_theme
        )

        self.__app.setStyle("windowsvista")
        self.__app.setStyleSheet(self.__cur_stylesheet)
        self.__app.setPalette(self.__cur_theme.to_qpalette(self.__app.palette()))

        if self.__icon_provider is None:
            self.__icon_provider = IconProvider(self.__cur_theme)
        else:
            self.__icon_provider.set_theme(self.__cur_theme)

        self.log.debug(f"Applied {ui_mode.name.lower()} theme to application.")
        self.theme_changed.emit(self.__cur_theme)

    def __resolve_ui_mode(self, ui_mode: UiMode) -> ResolvedUiMode:
        """
        Resolves the given UI mode to either dark or light.

        Args:
            ui_mode (UiMode): The UI mode to resolve.

        Returns:
            ResolvedUiMode: The resolved UI mode.
        """

        if ui_mode == UiMode.System:
            color_scheme: Qt.ColorScheme = self.__app.styleHints().colorScheme()

            if color_scheme == Qt.ColorScheme.Unknown:
                return UiMode.Dark

            return cast(ResolvedUiMode, UiMode.from_qt_color_scheme(color_scheme))

        else:
            return ui_mode

    def __on_color_scheme_changed(self, new_color_scheme: Qt.ColorScheme) -> None:
        """
        Slot for handling the color scheme change signal from the QApplication.

        Args:
            new_color_scheme (Qt.ColorScheme): The new color scheme.
        """

        if new_color_scheme == Qt.ColorScheme.Unknown:
            new_color_scheme = Qt.ColorScheme.Dark

        resolved_ui_mode: ResolvedUiMode = cast(
            ResolvedUiMode, UiMode.from_qt_color_scheme(new_color_scheme)
        )
        self.__set_ui_mode(resolved_ui_mode)

    @staticmethod
    def __add_font(font: str) -> None:
        """
        Adds a font to the QFontDatabase.

        Args:
            font (str): The path to the font file.

        Raises:
            RuntimeError: When failed to load the font.
        """

        font_id: int = QFontDatabase.addApplicationFont(font)

        if font_id == -1:
            raise RuntimeError(f"Failed to load font '{font}'!")

    @final
    @property
    def theme(self) -> Theme:
        """The current theme."""

        return self.__cur_theme

    @final
    @property
    def stylesheet(self) -> str:
        """The current stylesheet."""

        return self.__cur_stylesheet

    @final
    @property
    def ui_mode(self) -> UiMode:
        """The configured UI mode. Use `theme.ui_mode` to get the actual used UI mode."""

        return self.__ui_mode

    @final
    @classmethod
    def update_widget_styles(cls, widget: QWidget) -> None:
        """
        Updates the styles of the given widget by triggering a stylesheet recomputation.

        Args:
            widget (QWidget): The widget to update.
        """

        widget_stylesheet: str = widget.styleSheet()
        widget.setStyleSheet(cls.get().stylesheet)
        widget.setStyleSheet(widget_stylesheet)
