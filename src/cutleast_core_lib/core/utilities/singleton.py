"""
Copyright (c) Cutleast
"""

from abc import ABCMeta
from typing import ClassVar, Optional, Self, final

from PySide6.QtCore import QObject


class Singleton(metaclass=ABCMeta):
    """
    Base class providing singleton functionality:
    - only one instance of the class can exist at a time
    - `get()` method returns the singleton instance
    """

    __instance: ClassVar[Optional[Self]] = None

    def __init__(self, *, replace_existing_instance: bool = False) -> None:
        """
        Args:
            replace_existing_instance (bool, optional):
                Toggles whether to replace any existing instance. Defaults to False.

        Raises:
            RuntimeError:
                When the class is already initialized and `replace_existing_instance` is
                `False`.
        """

        cls = type(self)
        if (
            cls.__instance is not None
            and self is not cls.__instance
            and not replace_existing_instance
        ):
            raise RuntimeError(f"{cls.__name__} is already initialized!")

        cls.__instance = self

    @final
    @classmethod
    def has_instance(cls) -> bool:
        """
        Returns:
            bool: `True` if the class is initialized, `False` otherwise.
        """

        return cls.__instance is not None

    @final
    @classmethod
    def get_optional(cls) -> Optional[Self]:
        """
        Gets the current instance or returns None if the class is not initialized.

        Returns:
            Optional[Self]: The current instance or None.
        """

        return cls.__instance

    @final
    @classmethod
    def get(cls) -> Self:
        """
        Gets the current instance.

        Raises:
            RuntimeError: When the class is not initialized.

        Returns:
            Self: The current instance.
        """

        if cls.__instance is None:
            raise RuntimeError(f"{cls.__name__} is not initialized!")

        return cls.__instance


class SingletonQtMeta(type(QObject), type(Singleton)):  # pyright: ignore[reportGeneralTypeIssues]
    """
    Combined metaclass for Singleton + PySide6 Qt types to avoid metaclass conflicts.
    """


class SingletonQObject(QObject, Singleton, metaclass=SingletonQtMeta):
    """
    Base class for all QObjects subclasses that should be singletons.
    """
