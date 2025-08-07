"""
Copyright (c) Cutleast
"""


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

        color_code = color_code.removeprefix("#")

        if (len(color_code) == 6) or (len(color_code) == 8):
            try:
                int(color_code, 16)
                return True

            except ValueError:
                return False
        else:
            return False
