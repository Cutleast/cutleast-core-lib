"""
Copyright (c) Cutleast
"""

import logging
import platform
import subprocess
import sys
import time
from abc import ABCMeta, abstractmethod
from argparse import Namespace
from pathlib import Path
from typing import override

from PySide6.QtWidgets import QApplication, QMainWindow

from core.config.app_config import AppConfig
from core.utilities.exception_handler import ExceptionHandler
from core.utilities.exe_info import get_current_path
from core.utilities.logger import Logger
from core.utilities.updater import Updater
from ui.utilities.stylesheet_processor import StylesheetProcessor


class BaseApp(QApplication, metaclass=ABCMeta):
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

    stylesheet_processor: StylesheetProcessor
    """The stylesheet processor."""

    exception_handler: ExceptionHandler
    """The custom sys.excepthook handler redirecting exceptions to an ErrorDialog."""

    def __init__(self, args: Namespace) -> None:
        """
        Args:
            args (Namespace): Parsed commandline arguments passed to the application.
        """

        super().__init__()

        self.args = args

    @abstractmethod
    def init(self) -> None:
        """
        Initializes application.

        ### Implementations are required to set the following before calling this method:

        - `app_config`: The application config.
        - `applicationName()`: The application name.
        - `applicationVersion()`: The application version.
        - `main_window`: The main window of the application.
        """

        log_file: Path = self.log_path / time.strftime(self.app_config.log_file_name)
        self.logger = Logger(
            log_file, self.app_config.log_format, self.app_config.log_date_format
        )
        self.logger.setLevel(self.app_config.log_level)

        self.stylesheet_processor = StylesheetProcessor(self, self.app_config.ui_mode)
        self.exception_handler = ExceptionHandler(self)

        self._log_basic_info()
        self.app_config.print_settings_to_log()
        self.log.info("App started.")

    def _log_basic_info(self) -> None:
        """
        Logs basic information.
        """

        width = 100
        log_title = f" {self.applicationName()} ".center(width, "=")
        self.log.info(f"\n{'=' * width}\n{log_title}\n{'=' * width}")
        self.log.info(f"Program Version: {self.applicationVersion()}")
        self.log.info(f"Executed command: {subprocess.list2cmdline(sys.argv)}")
        self.log.info(f"Current Path: {self.cur_path}")
        self.log.info(f"Resource Path: {self.res_path}")
        self.log.info(f"Data Path: {self.data_path}")
        self.log.info(f"Log Path: {self.log_path}")
        self.log.info(
            "Detected Platform: "
            f"{platform.system()} {platform.version()} {platform.architecture()[0]}"
        )

    @override
    def exec(self) -> int:  # type: ignore
        """
        Executes application and shows main window.
        """

        try:
            Updater(
                self.get_repo_name(),
                self.get_repo_branch(),
                self.get_repo_owner(),
                self.applicationVersion(),
            ).run()
        except Exception as ex:
            self.log.warning(f"Failed to check for updates: {ex}", exc_info=ex)

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

    @abstractmethod
    @classmethod
    def get_repo_owner(cls) -> str:
        """
        Returns:
            str: GitHub repository owner.
        """

    @abstractmethod
    @classmethod
    def get_repo_name(cls) -> str:
        """
        Returns:
            str: GitHub repository name.
        """

    @abstractmethod
    @classmethod
    def get_repo_branch(cls) -> str:
        """
        Returns:
            str: GitHub repository branch.
        """
