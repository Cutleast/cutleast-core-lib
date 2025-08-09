"""
Copyright (c) Cutleast
"""

from abc import ABCMeta
from typing import ClassVar, Optional, Self, final


class Singleton(metaclass=ABCMeta):
    """
    Base class providing singleton functionality:
    - only one instance of the class can exist at a time
    - `get()` method returns the singleton instance
    """

    __instance: ClassVar[Optional[Self]] = None

    def __init__(self) -> None:
        """
        Raises:
            RuntimeError: When the class is already initialized.
        """

        cls = type(self)
        if cls.__instance is not None:
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
