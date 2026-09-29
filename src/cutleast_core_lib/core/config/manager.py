"""
Copyright (c) Cutleast
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generic, Optional, TypeVar

import jstyleson as json
from PySide6.QtCore import QObject, Signal

from .base_config import BaseConfig

T = TypeVar("T", bound=BaseConfig)
_T = TypeVar("_T", bound=BaseConfig)

_config_managers: dict[type[BaseConfig], ConfigManager] = {}


class ConfigManager(QObject, Generic[T]):
    """
    Manages a configuration instance.
    """

    changed = Signal()
    """Signal emitted when the managed configuration changes."""

    saved = Signal()
    """Signal emitted when the managed configuration is saved."""

    __config_cls: type[T]
    __config_path: Path
    __config: T

    __batch_edit_level: int

    log: logging.Logger

    def __init__(
        self, config_cls: type[T], config_path: Path, parent: Optional[QObject] = None
    ) -> None:
        """
        Args:
            config_cls (type[T]): Application configuration model to manage.
            config_path (Path): Path to the configuration directory.
            parent (Optional[QObject], optional):
                Optional parent object. Defaults to None.

        Raises:
            RuntimeError: If a config manager already exists for the specified class.
        """

        if config_cls in _config_managers:
            raise RuntimeError(
                "There is already an initialized config manager for "
                f"'{config_cls.__name__}'!"
            )

        super().__init__(parent)

        self.log = logging.getLogger(self.__class__.__name__)

        _config_managers[config_cls] = self

        self.__config_cls = config_cls
        self.__config_path = config_path
        self.__config = self.__load()

        self.__batch_edit_level = 0

        self.__config.set_change_callback(self.__on_config_changed)

    @property
    def config(self) -> T:
        """The managed configuration."""

        return self.__config

    def __load(self) -> T:
        """
        Loads configuration.

        Returns:
            T: Loaded configuration instance.
        """

        config_file_path: Path = self.__config_path / self.__config_cls.get_config_name()

        self.log.debug(f"Loading configuration from '{config_file_path}'...")

        config_data: dict[str, Any] = {}
        if config_file_path.is_file():
            config_data = json.loads(config_file_path.read_text(encoding="utf8"))
        else:
            self.log.debug(
                f"No config file at '{config_file_path}'. Falling back to "
                "default configuration..."
            )

        try:
            config: T = self.__config_cls.model_validate(config_data, by_alias=True)
        except Exception as ex:
            self.log.error(f"Failed to process user configuration: {ex}", exc_info=ex)
            config = self.__config_cls.model_validate({})

        self.log.info("Configuration loaded.")

        return config

    def save(self) -> None:
        """
        Saves the managed configuration.
        """

        config_file_path: Path = self.__config_path / self.__config_cls.get_config_name()

        self.log.debug(f"Saving configuration to '{config_file_path}'...")

        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        serialized: str = self.__config.model_dump_json(
            indent=4, by_alias=True, exclude_defaults=True
        )
        if serialized != r"{}":
            config_file_path.write_text(serialized, encoding="utf8")
            self.log.debug("Configuration saved.")
        else:
            config_file_path.unlink(missing_ok=True)
            self.log.debug("Deleted empty configuration file.")

        self.saved.emit()

    @contextmanager
    def edit(self) -> Generator[None]:
        """
        Batches configuration changes into one change notification.

        This can be nested where only the outermost edit emits a change notification
        on changes.
        """

        old_config: str = self.__config.model_dump_json()
        self.__batch_edit_level += 1

        try:
            yield
        finally:
            self.__batch_edit_level -= 1
            new_config: str = self.__config.model_dump_json()

            if self.__batch_edit_level == 0 and old_config != new_config:
                self.changed.emit()

    def __on_config_changed(self) -> None:
        """
        Handles a configuration change notification.
        """

        if not self.__batch_edit_level:
            self.changed.emit()

    def print_settings_to_log(self) -> None:
        """
        Prints current settings to log.
        """

        self.log.debug("Current Configuration:")
        keys: list[str] = list(
            filter(
                lambda f: (
                    BaseConfig.PropertyMarker.ExcludeFromLogging
                    not in self.__config_cls.get_property_markers(f)
                ),
                self.__config_cls.model_fields.keys(),
            )
        )
        indent: int = max(len(key) + 1 for key in keys)
        for key in keys:
            self.log.debug(f"{key.rjust(indent)} = '{getattr(self.__config, key)}'")

    @staticmethod
    def for_config_class(config_cls: type[_T]) -> ConfigManager[_T]:
        """
        Returns a configuration manager instance for the specified class.

        Args:
            config_cls (type[_T]): Application configuration model to manage.

        Returns:
            ConfigManager[_T]: Configuration manager instance.
        """

        return _config_managers[config_cls]
