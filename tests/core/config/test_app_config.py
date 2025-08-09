"""
Copyright (c) Cutleast
"""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic_core import ValidationError
from pyfakefs.fake_filesystem import FakeFilesystem

from cutleast_core_lib.core.config.app_config import AppConfig
from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.test.base_test import BaseTest


class TestAppConfig(BaseTest):
    """
    Tests `core.config.app_config.AppConfig`.
    """

    def test_load(self, test_fs: FakeFilesystem) -> None:
        """
        Tests `AppConfig.load()` with an empty user config.
        """

        # given
        user_config_path = Path("test_config")

        # when
        app_config: AppConfig = AppConfig.load(user_config_path)

        # then
        assert app_config.log_level == AppConfig.get_default_value(
            "log_level", Logger.Level
        )
        assert app_config.log_num_of_files == AppConfig.get_default_value(
            "log_num_of_files", int
        )

    def test_load_user_config(self, test_fs: FakeFilesystem) -> None:
        """
        Tests `AppConfig.load()` with a user config file.
        """

        # given
        user_config_path = Path("test_config")
        user_config_path.mkdir(parents=True, exist_ok=True)
        user_config_file_path = user_config_path / AppConfig.get_config_name()
        user_config_data: dict[str, Any] = {
            "log.level": "CRITICAL",
            "log.num_of_files": "10",
        }
        user_config_file_path.write_text(json.dumps(user_config_data), encoding="utf8")

        # when
        app_config: AppConfig = AppConfig.load(user_config_path)

        # then
        assert app_config.log_level == Logger.Level.Critical
        assert app_config.log_num_of_files == 10

        # when
        user_config_data = {"log.num_of_files": -2}
        user_config_file_path.write_text(json.dumps(user_config_data), encoding="utf8")
        app_config = AppConfig.load(user_config_path)

        # then
        assert app_config.log_num_of_files == 5

    def test_save_user_config(self, test_fs: FakeFilesystem) -> None:
        """
        Tests `AppConfig.save()`.
        """

        # given
        user_config_path = Path("test_config")
        user_config_path.mkdir(parents=True, exist_ok=True)
        app_config: AppConfig = AppConfig.load(user_config_path)

        # when
        app_config.log_level = Logger.Level.Critical
        app_config.save()

        # then
        app_config: AppConfig = AppConfig.load(user_config_path)
        assert app_config.log_level == Logger.Level.Critical

        # when
        app_config.log_level = app_config.get_default_value("log_level", Logger.Level)
        app_config.save()

        # then
        assert not (user_config_path / AppConfig.get_config_name()).exists()

    def test_log_num_validation(self) -> None:
        """
        Tests `AppConfig.log_num_of_files` validation.
        """

        # given
        app_config: AppConfig = AppConfig.load(Path("test_config"))

        # when/then
        app_config.log_num_of_files = -1
        with pytest.raises(ValidationError):
            app_config.log_num_of_files = -2

        app_config.log_num_of_files = 1
