"""
Copyright (c) Cutleast
"""

import logging
from abc import ABCMeta, abstractmethod
from typing import Literal, Optional, final

import darkdetect
from PySide6.QtGui import QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

from cutleast_core_lib.core.utilities.singleton import Singleton

from .icon_provider import IconProvider
from .ui_mode import UIMode


class ThemeManager(Singleton, metaclass=ABCMeta):
    """
    Singleton class for managing the application theme and fonts.
    """

    log: logging.Logger = logging.getLogger("ThemeManager")

    _accent_color: str
    _ui_mode: UIMode
    _fonts: list[str]
    _icon_provider: IconProvider
    _stylesheet: Optional[str] = None

    def __init__(
        self, accent_color: str, ui_mode: UIMode, fonts: list[str] = []
    ) -> None:
        """
        Args:
            accent_color (str): The user-configured accent color.
            ui_mode (UIMode): The user-configured UI mode.
            fonts (list[str], optional): The application fonts. Defaults to [].

        Raises:
            RuntimeError: When the class is already initialized.
        """

        super().__init__()

        self._accent_color = accent_color
        self._ui_mode = ui_mode
        self._fonts = fonts
        self._icon_provider = self._init_icon_provider()

    def _load_fonts(self) -> None:
        """
        Loads fonts and adds them to the QFontDatabase.

        Raises:
            RuntimeError: When failed to load a font.
        """

        self.log.info("Loading fonts...")

        for font in self._fonts:
            self.log.debug(f"Loading font '{font}'...")
            ThemeManager.add_font(font)

        self.log.info(f"Loaded {len(self._fonts)} fonts.")

    @final
    @staticmethod
    def add_font(font: str) -> None:
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

    @abstractmethod
    def _get_stylesheet(self) -> str:
        """
        Gets the stylesheet for the current UI mode and accent color.

        Returns:
            str: The stylesheet.
        """

    @abstractmethod
    def _apply_to_palette(self, palette: QPalette) -> None:
        """
        Applies the theme for the current UI mode and accent color to a QPalette.

        Args:
            palette (QPalette):
                The palette to apply the theme to. Usually the one from the QApplication.
        """

    @abstractmethod
    def _init_icon_provider(self) -> IconProvider:
        """
        Initializes the icon provider for the current UI mode.

        Returns:
            IconProvider: The icon provider.
        """

    def apply_to_app(self, app: QApplication) -> None:
        """
        Applies theme, fonts and palette to the QApplication.

        Args:
            app (QApplication): The QApplication to apply the theme to.
        """

        self._stylesheet = self._get_stylesheet()
        app.setStyleSheet(self._stylesheet)

        palette = app.palette()
        self._apply_to_palette(palette)
        app.setPalette(palette)

        self._load_fonts()

        self.log.info(f"Applied {self.ui_mode.name.lower()} theme to application.")

    @final
    @property
    def ui_mode(self) -> Literal[UIMode.Dark, UIMode.Light]:
        """The current UI mode."""

        ui_mode: UIMode
        if self._ui_mode == UIMode.System:
            ui_mode = self.detect_system_ui_mode()
        else:
            ui_mode = self._ui_mode

        return ui_mode

    @classmethod
    def detect_system_ui_mode(cls) -> Literal[UIMode.Light, UIMode.Dark]:
        """
        Detects system UI mode. Returns `UIMode.Dark` if detection fails.

        Returns:
            Literal[UIMode.Light, UIMode.Dark]: Detected UI mode.
        """

        system_mode: Optional[str] = darkdetect.theme()

        match system_mode:
            case "Light":
                return UIMode.Light
            case "Dark":
                return UIMode.Dark
            case None:
                cls.log.warning("Failed to detect system UI mode!")
            case unknown:
                cls.log.warning(f"Unknown system UI mode {unknown!r}!")

        return UIMode.Dark

    @classmethod
    def get_stylesheet(cls) -> Optional[str]:
        """
        Returns:
            Optional[str]: Current stylesheet or None if the class is not initialized.
        """

        if cls.has_instance():
            return cls.get()._stylesheet
