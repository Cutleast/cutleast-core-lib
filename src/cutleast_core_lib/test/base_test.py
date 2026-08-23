"""
Copyright (c) Cutleast

**Importing this module will prevent Qt from rendering widgets on screen.**
"""

import os
import sys
from abc import ABCMeta
from collections.abc import Generator
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from PySide6.QtWidgets import QApplication

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.config.app_config import AppConfig
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.theme.ui_mode import UiMode
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider

from .setup.clipboard_mock import ClipboardMock

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # render widgets off-screen


class BaseTest(metaclass=ABCMeta):
    """
    Base class for tests.
    """

    @pytest.fixture
    def data_folder(self) -> Path:
        """
        Returns the path to the test data folder.

        Returns:
            Path: The path to the test data folder.
        """

        return Path("tests").absolute() / "data"

    @pytest.fixture
    def real_cwd(self) -> Path:
        """
        Returns:
            Path: The real current working directory (outside of the fake filesystem).
        """

        return Path.cwd()

    @pytest.fixture(name="test_fs")
    def _base_test_fs(self, data_folder: Path, fs: FakeFilesystem) -> FakeFilesystem:
        """
        Creates a fake filesystem for testing and adds required files.

        Returns:
            FakeFilesystem: The fake filesystem.
        """

        fs.add_real_directory(data_folder)

        # Add the active virtual environment.
        fs.add_real_directory(Path(sys.prefix))

        return fs

    @pytest.fixture(name="app_config")
    def _base_app_config(self, data_folder: Path) -> AppConfig:
        """
        Returns the application config for the tests.

        Returns:
            AppConfig: The application config.
        """

        return AppConfig.load(data_folder / "config")

    @pytest.fixture(autouse=True)
    def _theme_manager(self, qapp: QApplication) -> Generator[ThemeManager]:
        """
        Provides an initialized theme manager and icon provider for UI tests.
        """

        if ThemeManager.has_instance():
            yield ThemeManager.get()
            return

        theme_manager = ThemeManager(qapp, "#ffffff", UiMode.Dark)

        yield theme_manager

        Utils.reset_singleton(IconProvider)
        Utils.reset_singleton(ThemeManager)

    @pytest.fixture
    def cache(self, test_fs: FakeFilesystem) -> Cache:
        """
        Returns the cache for the tests. Initializes it with the fake filesystem, if
        needed.

        Args:
            test_fs (FakeFilesystem): The fake filesystem.

        Returns:
            Cache: The cache.
        """

        return Cache.get_optional() or Cache(Path("test_cache"), "development")

    @pytest.fixture
    def clipboard(self, monkeypatch: pytest.MonkeyPatch) -> Generator[ClipboardMock]:
        """
        Fixture to mock the clipboard using `setup.clipboard.Clipboard`.
        Patches `QtGui.QClipboard.setText` and `QtGui.QClipboard.text`.

        Args:
            monkeypatch (pytest.MonkeyPatch): The MonkeyPatch fixture.

        Yields:
            Generator[ClipboardMock, None, None]: The mocked clipboard.
        """

        clipboard_mock = ClipboardMock()

        monkeypatch.setattr(
            "PySide6.QtWidgets.QApplication.clipboard",
            lambda: clipboard_mock,
        )

        yield clipboard_mock
