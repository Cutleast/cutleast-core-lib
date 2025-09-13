"""
Copyright (c) Cutleast
"""

import logging
import os
from abc import ABCMeta, abstractmethod
from pathlib import Path

from cutleast_core_lib.core.utilities.filesystem import str_glob

from ..utilities.process_runner import run_process


class Archive(metaclass=ABCMeta):
    """
    Base class for archives.

    **Requires the 7-zip executable to be present at `res/7-zip/7z.exe`!**

    **Do not instantiate directly, use Archive.load_archive() instead!**
    """

    _bin_path = Path("res") / "7-zip" / "7z.exe"

    log: logging.Logger = logging.getLogger("Archive")

    def __init__(self, path: Path) -> None:
        self.path = path

    @property
    @abstractmethod
    def files(self) -> list[str]:
        """
        Gets a list of files in the archive.

        Returns:
            list[str]: List of filenames, relative to archive root.
        """

    def get_files(self) -> list[str]:
        """
        Alias method for `Archive.files` property.

        Returns:
            list[str]: List of filenames, relative to archive root.
        """

        return self.files

    def extract_all(self, dest: Path, full_paths: bool = True) -> None:
        """
        Extracts archive content.

        Args:
            dest (Path): Folder to extract archive content to.
            full_paths (bool, optional):
                Toggles whether paths within archive are retained. Defaults to True.

        Raises:
            RuntimeError: When the 7-zip commandline returns a non-zero exit code.
        """

        cmd: list[str] = [
            str(Archive._bin_path),
            "x" if full_paths else "e",
            str(self.path),
            f"-o{dest}",
            "-aoa",
            "-y",
        ]

        run_process(cmd)

    def extract(self, filename: str, dest: Path, full_paths: bool = True) -> None:
        """
        Extracts a single file.

        Args:
            filename (str): Filename of file to extract.
            dest (Path): Folder to extract file to.
            full_paths (bool, optional):
                Toggles whether path within archives is retained. Defaults to True.

        Raises:
            RuntimeError: When the 7-zip commandline returns a non-zero exit code.
        """

        cmd: list[str] = [
            str(Archive._bin_path),
            "x" if full_paths else "e",
            f"-o{dest}",
            "-aoa",
            "-y",
            "--",
            str(self.path),
            filename,
        ]

        run_process(cmd)

    def extract_files(
        self, filenames: list[str], dest: Path, full_paths: bool = True
    ) -> None:
        """
        Extracts multiple files.

        Args:
            filenames (list[str]): List of filenames to extract.
            dest (Path): Folder to extract files to.
            full_paths (bool, optional):
                Toggles whether paths within archive are retained. Defaults to True.

        Raises:
            RuntimeError: When the 7-zip commandline returns a non-zero exit code.
        """

        if not len(filenames):
            return

        cmd: list[str] = [
            str(Archive._bin_path),
            "x" if full_paths else "e",
            f"-o{dest}",
            "-aoa",
            "-y",
            str(self.path),
        ]

        # Write filenames to a txt file to workaround commandline length limit
        filenames_txt = self.path.with_suffix(".txt")
        with open(filenames_txt, "w", encoding="utf8") as file:
            file.write("\n".join(filenames))
        cmd.append(f"@{filenames_txt}")

        try:
            run_process(cmd)
        except RuntimeError:
            os.remove(filenames_txt)
            raise

    def glob(self, pattern: str) -> list[str]:
        """
        Gets a list of file paths that match a specified pattern.

        Args:
            pattern (str): Pattern that matches everything that fnmatch supports

        Returns:
            list: List of matching filenames.
        """

        matches: list[str] = str_glob(pattern, list(self.files))
        return matches

    @staticmethod
    def load_archive(archive_path: Path) -> "Archive":
        """
        Loads archive with fitting handler class.

        Currently supported archive types: RAR, 7z, ZIP

        Args:
            archive_path (Path): Path to archive file.

        Raises:
            NotImplementedError: When the archive type is not supported.

        Returns:
            Archive: Correct initialized handler class to use.
        """

        from .rar import RARArchive
        from .sevenzip import SevenZipArchive
        from .zip import ZIPARchive

        match archive_path.suffix.lower():
            case ".rar":
                return RARArchive(archive_path)
            case ".7z":
                return SevenZipArchive(archive_path)
            case ".zip":
                return ZIPARchive(archive_path)
            case suffix:
                raise NotImplementedError(
                    f"Archive format {suffix!r} not yet supported!"
                )
