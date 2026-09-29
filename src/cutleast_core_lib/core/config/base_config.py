"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from enum import Enum, auto
from typing import Any, Optional, TypeVar, get_origin, get_type_hints, override

from pydantic import ConfigDict, PrivateAttr
from pydantic.fields import FieldInfo

from ..utilities.dynamic_default_model import DynamicDefaultModel

T = TypeVar("T", bound="BaseConfig")
V = TypeVar("V")
_MISSING = object()


class BaseConfig(DynamicDefaultModel, metaclass=ABCMeta):
    """
    Base class for app configurations.
    """

    class PropertyMarker(Enum):
        """Enum for custom property markers to be applied to pydantic fields."""

        ExcludeFromLogging = auto()
        """The field is excluded from logging."""

    model_config = ConfigDict(validate_assignment=True)

    _change_callback: Optional[Callable[[], None]] = PrivateAttr(default=None)

    def set_change_callback(self, callback: Callable[[], None]) -> None:
        """
        Sets a callback function to be called when the configuration changes.

        Args:
            callback (Callable[[], None]): Callback function to be called.
        """

        self._change_callback = callback

    def notify_changes(self) -> None:
        """
        Notifies registered consumers about configuration changes.
        """

        if self._change_callback is not None:
            self._change_callback()

    @override
    def __setattr__(self, name: str, value: object) -> None:
        old_value: object = getattr(self, name, _MISSING)

        super().__setattr__(name, value)

        if name not in type(self).model_fields:
            return

        if old_value != getattr(self, name):
            self.notify_changes()

    @staticmethod
    @abstractmethod
    def get_config_name() -> str:
        """
        Returns the name of the configuration file.

        Returns:
            str: Name of the configuration file.
        """

    @classmethod
    def get_property_markers(cls, field_name: str) -> list[PropertyMarker]:
        """
        Returns the property markers for a field.

        Args:
            field_name (str): Name of the field.

        Raises:
            AttributeError: If the field doesn't exist.

        Returns:
            list[PropertyMarker]: List of property markers.
        """

        fields: dict[str, Any] = get_type_hints(cls, include_extras=True)

        if field_name not in fields:
            raise AttributeError(f"Field '{field_name}' does not exist.")

        field = fields[field_name]
        metadata: list[Any] = getattr(field, "__metadata__", [])

        markers: list[BaseConfig.PropertyMarker] = [
            item for item in metadata if isinstance(item, BaseConfig.PropertyMarker)
        ]

        return markers

    @classmethod
    def get_default_value(cls, field_name: str, expected_type: type[V]) -> V:
        """
        Attempts to get the default value of the specified field.
        Validates the type of the default value.

        Args:
            field_name (str): Name of the field.
            expected_type (type[V]): Expected type of the default value.

        Raises:
            AttributeError: If the field doesn't exist.
            ValueError: If the default value is not of the expected type.

        Returns:
            V: Default value of the field.
        """

        if field_name not in cls.model_fields:
            raise AttributeError(f"Field '{field_name}' does not exist.")

        field: FieldInfo = cls.model_fields[field_name]
        default_value: Any = field.get_default(call_default_factory=True)

        if not isinstance(default_value, get_origin(expected_type) or expected_type):
            raise TypeError(
                f"'{field_name}' ({type(default_value)}) is not a {expected_type}!"
            )

        return default_value
