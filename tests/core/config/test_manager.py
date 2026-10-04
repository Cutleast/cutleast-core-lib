"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

from cutleast_core_lib.core.config.base_config import BaseConfig
from cutleast_core_lib.core.config.manager import ConfigManager
from cutleast_core_lib.test.base_test import BaseTest
from pydantic import Field
from pytestqt.qtbot import QtBot


class TestConfigManager(BaseTest):
    """
    Tests `core.config.manager.ConfigManager`.
    """

    class _MyConfig(BaseConfig):
        value1: int = 42
        value2: str = "Hello"
        value3: list[str] = Field(default_factory=list)

        @override
        @staticmethod
        def get_config_name() -> str:
            return "my_config.json"

    class _AnotherConfig(BaseConfig):
        @override
        @staticmethod
        def get_config_name() -> str:
            return "another_config.json"

    def test_for_config_class(self, tmp_path: Path) -> None:
        """
        Tests `ConfigManager.for_config_class`.
        """

        # given
        manager = ConfigManager(TestConfigManager._MyConfig, tmp_path)

        # when
        actual_manager: ConfigManager[TestConfigManager._MyConfig] = (
            ConfigManager.for_config_class(TestConfigManager._MyConfig)
        )

        # then
        assert actual_manager is manager

    def test_multiple_config_managers(self, tmp_path: Path) -> None:
        """
        Tests multiple ConfigManager instances for different config models.
        """

        # given
        my_manager = ConfigManager(TestConfigManager._MyConfig, tmp_path)
        another_manager = ConfigManager(TestConfigManager._AnotherConfig, tmp_path)

        # when
        actual_my_manager: ConfigManager[TestConfigManager._MyConfig] = (
            ConfigManager.for_config_class(TestConfigManager._MyConfig)
        )
        actual_another_manager: ConfigManager[TestConfigManager._AnotherConfig] = (
            ConfigManager.for_config_class(TestConfigManager._AnotherConfig)
        )

        # then
        assert actual_my_manager is my_manager
        assert actual_another_manager is another_manager

    def test_batch_edit(self, tmp_path: Path, qtbot: QtBot) -> None:
        """
        Tests the `ConfigManager.edit()` context manager.
        """

        # given
        my_manager = ConfigManager(TestConfigManager._MyConfig, tmp_path)
        calls: list[int] = []
        my_manager.changed.connect(lambda: calls.append(1))

        # when
        with my_manager.edit():
            my_manager.config.value1 = 43
            my_manager.config.value2 = "World"

        # then
        assert calls == [1]

    def test_batch_edit_nested(self, tmp_path: Path, qtbot: QtBot) -> None:
        """
        Tests the `ConfigManager.edit()` context manager with nested edits.
        """

        # given
        my_manager = ConfigManager(TestConfigManager._MyConfig, tmp_path)
        calls: list[int] = []
        my_manager.changed.connect(lambda: calls.append(1))

        # when
        with my_manager.edit():
            my_manager.config.value1 = 43

            with my_manager.edit():
                my_manager.config.value2 = "World"

        # then
        assert calls == [1]

    def test_batch_edit_no_change(self, tmp_path: Path, qtbot: QtBot) -> None:
        """
        Tests the `ConfigManager.edit()` context manager without any changes.
        """

        # given
        my_manager = ConfigManager(TestConfigManager._MyConfig, tmp_path)
        calls: list[int] = []
        my_manager.changed.connect(lambda: calls.append(1))

        # when
        with my_manager.edit():
            pass

        # then
        assert calls == []

    def test_dirty(self, tmp_path: Path, qtbot: QtBot) -> None:
        """
        Tests the `ConfigManager.dirty` property on changes.
        """

        # given
        my_manager = ConfigManager(TestConfigManager._MyConfig, tmp_path)

        # then
        assert not my_manager.dirty

        # when
        my_manager.config.value1 = 43

        # then
        assert my_manager.dirty

        # when
        my_manager.save()

        # then
        assert not my_manager.dirty

        # when
        with my_manager.edit():
            pass

        # then
        assert not my_manager.dirty

        # when
        my_manager.config.value1 = 43

        # then
        assert not my_manager.dirty
