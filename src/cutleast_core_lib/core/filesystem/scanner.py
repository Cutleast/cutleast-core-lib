"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path

from virtual_glob import InMemoryPath
from virtual_glob import glob as vglob

from .file import File


class DirectoryScanner:
    """
    Class for scanning directories and collecting file information.
    """

    log: logging.Logger = logging.getLogger("DirectoryScanner")

    @classmethod
    def scan_folder(
        cls, folder: Path, recursive: bool = True, ignore_errors: bool = True
    ) -> list[File]:
        """
        Collects all files in a folder and returns them.

        Args:
            folder (Path): The folder to collect files from.
            recursive (bool):
                Whether to collect files recursively from subfolders. Defaults to True.
            ignore_errors (bool):
                Whether to ignore errors when accessing files/folders. Defaults to True.

        Raises:
            Exception:
                When an error occurs while scanning the folder and `ignore_errors` is
                False.

        Returns:
            list[File]: List of File instances representing the files in the folder.
        """

        result: list[File] = []

        for entry in os.scandir(folder):
            entry_path = Path(entry.path)

            try:
                if entry.is_dir() and recursive:
                    result.extend(cls.scan_folder(entry_path, recursive))
                elif entry.is_file():
                    result.append(File._from_dir_entry(entry))  # pyright: ignore[reportPrivateUsage]

            except Exception as ex:
                cls.log.error(f"Failed to scan '{entry_path}': {ex}", exc_info=ex)
                if not ignore_errors:
                    raise ex

        return result

    @classmethod
    def glob_folder(
        cls,
        folder: Path,
        pattern: str,
        recursive: bool = True,
        ignore_errors: bool = True,
    ) -> list[File]:
        """
        Collects all files in a folder matching a glob pattern and returns them.

        Args:
            folder (Path): The folder to collect files from.
            pattern (str): The glob pattern to match files.
            recursive (bool):
                Whether to collect files recursively from subfolders. Defaults to True.
            ignore_errors (bool):
                Whether to ignore errors when accessing files/folders. Defaults to True.

        Raises:
            Exception:
                When an error occurs while scanning the folder and `ignore_errors` is
                False.

        Returns:
            list[File]:
                List of File instances representing the files that match the pattern in
                the folder.
        """

        case_sensitive: bool = os.name != "nt"  # Case insensitive on Windows

        files: list[File] = cls.scan_folder(folder, recursive, ignore_errors)

        file_map: dict[str, File]
        if case_sensitive:
            file_map = {str(file.path): file for file in files}
        else:
            file_map = {str(file.path).lower(): file for file in files}
            pattern = pattern.lower()

        fs: InMemoryPath = InMemoryPath.from_list(list(file_map.keys()))
        matches: list[File] = [
            file_map[p.path] for p in vglob(fs, pattern) if p.path in file_map
        ]

        return matches

    @classmethod
    def get_folder_size(cls, folder: Path, recursive: bool = True) -> int:
        """
        Calculates the total size of all files in a folder.

        This method is more efficient for calculating the size of an entire folder than the traditional
        ```
        for path in folder.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size
        ```
        as it only makes a single call to the filesystem per file, rather than two.

        Args:
            folder (Path): The folder to calculate the size of.
            recursive (bool):
                Whether to include files from subfolders. Defaults to True.

        Returns:
            int: The total size of all files in bytes.
        """

        return sum(file.size for file in cls.scan_folder(folder, recursive))
