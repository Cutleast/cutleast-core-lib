"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path
from typing import Self, override

from pydantic import BaseModel

from ..utilities.scale import scale_value
from .utils import get_file_identifier, open_in_explorer


class File(BaseModel, frozen=True):
    """
    Immutable model representing a file with its path, size, other attributes preloaded
    and some utility methods.

    This model is not meant to be initialized outside of the DirectoryScanner class.
    """

    path: Path
    """The path to the file."""

    size: int
    """The size of the file in bytes."""

    last_modified: float
    """The timestamp of the last modification of the file."""

    creation_time: float
    """The timestamp when the file was created."""

    @classmethod
    def _from_dir_entry(cls, entry: os.DirEntry[str]) -> Self:
        """
        Creates a File instance from a given `os.DirEntry`.

        Args:
            entry (os.DirEntry[str]): The directory entry representing the file.

        Raises:
            ValueError: If the entry is not a file.

        Returns:
            File: A File instance representing the file.
        """

        if not entry.is_file():
            raise ValueError(f"Entry '{entry.path}' is not a file.")

        creation_time: float
        try:
            creation_time = entry.stat().st_birthtime
        except AttributeError:
            creation_time = entry.stat().st_mtime

        return cls(
            path=Path(entry.path),
            size=entry.stat().st_size,
            last_modified=entry.stat().st_mtime,
            creation_time=creation_time,
        )

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self.path == other.path

    @override
    def __hash__(self) -> int:
        return self.path.__hash__()

    @override
    def __repr__(self) -> str:
        return f"{self.path} ({scale_value(self.size)})"

    def get_identifier(self) -> str:
        """
        Generates a unique identifier for this file.

        Returns:
            str: A unique identifier for this file.
        """

        return get_file_identifier(self.path)

    def open(self) -> None:
        """
        Opens this file with the system's default applicaton.
        """

        os.startfile(self.path)

    def open_in_explorer(self) -> None:
        """
        Opens this file location in the system's file explorer.
        """

        open_in_explorer(self.path)
