"""
Copyright (c) Cutleast

**Importing this module will prevent Qt from rendering widgets on screen.**
"""

import os
from abc import ABCMeta
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.config.app_config import AppConfig
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.utilities.ui_mode import UIMode

from .setup.clipboard_mock import ClipboardMock

os.environ["QT_QPA_PLATFORM"] = "offscreen"  # render widgets off-screen

IconProvider(UIMode.Dark, "#ffffff")  # make sure that the icon provider is initialized


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
    def _base_test_fs(
        self, real_cwd: Path, data_folder: Path, fs: FakeFilesystem
    ) -> FakeFilesystem:
        """
        Creates a fake filesystem for testing and adds required files.

        Returns:
            FakeFilesystem: The fake filesystem.
        """

        fs.add_real_directory(data_folder)

        # Add venv
        fs.add_real_directory(real_cwd / ".venv")

        return fs

    @pytest.fixture(name="app_config")
    def _base_app_config(self, data_folder: Path) -> AppConfig:
        """
        Returns the application config for the tests.

        Returns:
            AppConfig: The application config.
        """

        return AppConfig.load(data_folder / "config")

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
    def clipboard(self, monkeypatch: pytest.MonkeyPatch) -> ClipboardMock:
        """
        Fixture to mock the clipboard using `setup.clipboard.Clipboard`.
        Patches `QtGui.QClipboard.setText` and `QtGui.QClipboard.text`.

        Args:
            monkeypatch (pytest.MonkeyPatch): The MonkeyPatch fixture.

        Returns:
            ClipboardMock: The mocked clipboard.
        """

        clipboard_mock = ClipboardMock()

        monkeypatch.setattr("PySide6.QtGui.QClipboard.setText", clipboard_mock.copy)
        monkeypatch.setattr("PySide6.QtGui.QClipboard.text", clipboard_mock.paste)

        return clipboard_mock
