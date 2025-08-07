"""
Copyright (c) Cutleast
"""

from typing import override

from ..utilities.exceptions import LocalizedException


class ConfigValidationError(LocalizedException):
    """
    Exception when the config is invalid.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)

    @override
    def getLocalizedMessage(self) -> str:
        return "{0}"
