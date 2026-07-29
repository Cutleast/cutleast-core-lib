"""
Copyright (c) Cutleast
"""

from pathlib import Path

from PySide6.QtWidgets import QApplication

from cutleast_core_lib.core.config.exceptions import ConfigValidationError


class ValidationUtils:
    """
    Helper class for validating user input.
    """

    @classmethod
    def is_valid_hex_color(cls, color_code: str) -> bool:
        """
        Checks if a string is a valid hex color code.

        Args:
            color_code (str): String to check.

        Returns:
            bool: `True` if string is a valid hex color code, `False` otherwise.
        """

        if not color_code.startswith("#"):
            return False

        color_code = color_code.removeprefix("#")

        if (len(color_code) == 6) or (len(color_code) == 8):
            try:
                int(color_code, 16)
                return True

            except ValueError:
                return False
        else:
            return False

    @classmethod
    def validate_hex_color(cls, color_code: str) -> str:
        """
        Validates a hex color code. This validator method is compatible with Pydantic
        field validators and can be used as such.

        Args:
            color_code (str): String to validate.

        Raises:
            ValueError: If the string is not a valid hex color code.

        Returns:
            str: The validated hex color code.
        """

        if not cls.is_valid_hex_color(color_code):
            raise ValueError(f"'{color_code}' is not a valid hex color code.")

        return color_code

    @classmethod
    def validate_parent_path(cls, path_input: str) -> None:
        """
        Validates if the parent of a path exists, if a path is specified at all. Does
        nothing if the path is empty.

        Args:
            path_input (str): The path to validate.
        """

        if path_input.strip():
            path = Path(path_input.strip())
            if not path.parent.is_dir():
                raise ConfigValidationError(
                    QApplication.translate(
                        "ValidationUtils", "The path '{path}' does not exist!"
                    ).format(path=path.parent)
                )
