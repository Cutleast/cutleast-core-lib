"""
Copyright (c) Cutleast
"""

import logging
import platform
import time
from abc import ABCMeta, abstractmethod
from argparse import Namespace
from pathlib import Path
from typing import Optional, override

from PySide6.QtWidgets import QApplication, QMainWindow

from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.utilities.ui_mode import UIMode

from .core.config.app_config import AppConfig
from .core.utilities.exception_handler import ExceptionHandler
from .core.utilities.exe_info import get_current_path, get_execution_info
from .core.utilities.logger import Logger
from .core.utilities.updater import Updater
from .ui.utilities.theme_manager import ThemeManager


class ABCQtMeta(type(QApplication), ABCMeta):  # pyright: ignore[reportGeneralTypeIssues]
    """
    Combined metaclass for ABC + PySide6 Qt types to avoid metaclass conflicts.
    """


class BaseApp(QApplication, metaclass=ABCQtMeta):
    """
    Abstract base class for the main application.
    """

    args: Namespace
    """Arguments passed to the application."""

    cur_path: Path = get_current_path()
    """
    The current path to the application (working dir in source form and executable path
    when compiled).
    """

    app_config: AppConfig
    """The application config."""

    data_path: Path = cur_path / "data"
    """Path to the user data folder."""

    res_path: Path = cur_path / "res"
    """Path to the application resources."""

    config_path: Path = data_path / "config"
    """Path to the user configuration folder."""

    log: logging.Logger = logging.getLogger("App")
    """The application logger."""

    logger: Logger
    """The root logger."""

    log_path: Path = data_path / "logs"
    """Path to the application logs folder."""

    main_window: QMainWindow
    """The main window of the application."""

    theme_manager: Optional[ThemeManager]
    """The theme manager."""

    exception_handler: ExceptionHandler
    """The custom sys.excepthook handler redirecting exceptions to an ErrorDialog."""

    def __init__(self, args: Namespace) -> None:
        """
        Args:
            args (Namespace): Parsed commandline arguments passed to the application.
        """

        super().__init__()

        self.args = args

        self._init()

    @abstractmethod
    def _init(self) -> None:
        """
        Initializes application.

        ### Implementations are required to set the following before calling this method:

        - `applicationName()`: The application name.
        - `applicationVersion()`: The application version.
        """

        self.setApplicationDisplayName(
            f"{self.applicationName()} v{self.applicationVersion()}"
        )

        self.app_config = self._load_app_config()

        log_file: Path = self.log_path / time.strftime(self.app_config.log_file_name)
        self.logger = Logger(
            log_file, self.app_config.log_format, self.app_config.log_date_format
        )
        self.logger.setLevel(self.app_config.log_level)
        self.exception_handler = ExceptionHandler(self)

        self.theme_manager = self._get_theme_manager()
        if self.theme_manager is not None:
            self.theme_manager.apply_to_app(self)
        # Make sure that the icon provider is initialized without a theme manager
        else:
            ui_mode = self.app_config.ui_mode
            if ui_mode == UIMode.System:
                ui_mode = ThemeManager.detect_system_ui_mode()

            IconProvider(ui_mode, "#ffffff" if ui_mode == UIMode.Dark else "#000000")

        self.main_window = self._init_main_window()

        self._log_basic_info()
        self.app_config.print_settings_to_log()
        self.log.info("App started.")

    @abstractmethod
    def _load_app_config(self) -> AppConfig:
        """
        Loads the application config.

        Returns:
            AppConfig: The application config.
        """

    @abstractmethod
    def _get_theme_manager(self) -> Optional[ThemeManager]:
        """
        Gets the theme manager.

        Returns:
            Optional[ThemeManager]: The theme manager.
        """

    @abstractmethod
    def _init_main_window(self) -> QMainWindow:
        """
        Initializes the main window of the application.

        Returns:
            QMainWindow: The main window of the application.
        """

    def _log_basic_info(self) -> None:
        """
        Logs basic information.
        """

        width = 100
        log_title = f" {self.applicationName()} ".center(width, "=")
        self.log.info(f"\n{'=' * width}\n{log_title}\n{'=' * width}")
        self.log.info(f"Program Version: {self.applicationVersion()}")
        self.log.info(f"Executed command: {get_execution_info()[0]}")
        self.log.info(f"Frozen/compiled: {get_execution_info()[1]}")
        self.log.info(f"Current Path: {self.cur_path}")
        self.log.info(f"Resource Path: {self.res_path}")
        self.log.info(f"Data Path: {self.data_path}")
        self.log.info(f"Log Path: {self.log_path}")
        self.log.info(
            "Detected Platform: "
            f"{platform.system()} {platform.version()} {platform.architecture()[0]}"
        )

    def check_for_updates(self) -> None:
        """
        Runs the updater if `get_repo_name()`, `get_repo_branch()` and
        `get_repo_owner()` do not return None.
        """

        repo_name: Optional[str] = self.get_repo_name()
        repo_branch: Optional[str] = self.get_repo_branch()
        repo_owner: Optional[str] = self.get_repo_owner()

        if not repo_name or not repo_branch or not repo_owner:
            return

        try:
            Updater(repo_name, repo_branch, repo_owner, self.applicationVersion()).run()
        except Exception as ex:
            self.log.warning(f"Failed to check for updates: {ex}", exc_info=ex)

    @override
    def exec(self, show_main_window: bool = True) -> int:  # type: ignore
        """
        Executes application and shows main window.

        Args:
            show_main_window (bool, optional):
                Whether to show the main window. Defaults to True.

        Returns:
            int: Application return code.
        """

        self.check_for_updates()

        if show_main_window:
            self.main_window.show()

        retcode: int = super().exec()

        self.clean()

        self.log.info("Exiting application...")

        return retcode

    @override
    def exit(self, retcode: int = 0) -> bool:  # type: ignore
        """
        Exits application.

        Returns:
            bool: Whether the application was exited or the user chose to cancel.
        """

        if self.main_window.close():
            super().exit(retcode)
            return True

        return False

    def clean(self) -> None:
        """
        Cleans up and exits application.
        """

        self.log.info("Cleaning...")

        # Clean up log files
        self.logger.clean_log_folder(
            self.log_path,
            self.app_config.log_file_name,
            self.app_config.log_num_of_files,
        )

    @classmethod
    @abstractmethod
    def get_repo_owner(cls) -> Optional[str]:
        """
        Returns:
            Optional[str]: GitHub repository owner.
        """

    @classmethod
    @abstractmethod
    def get_repo_name(cls) -> Optional[str]:
        """
        Returns:
            Optional[str]: GitHub repository name.
        """

    @classmethod
    @abstractmethod
    def get_repo_branch(cls) -> Optional[str]:
        """
        Returns:
            Optional[str]: GitHub repository branch.
        """
