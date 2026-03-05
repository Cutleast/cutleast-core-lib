"""
Copyright (c) Cutleast
"""

import datetime
import logging
import os
import shutil
import subprocess
import time
import uuid
from io import BufferedReader, RawIOBase
from pathlib import Path
from typing import Any, BinaryIO, Literal, override

from cutleast_core_lib.core.utilities.exe_info import get_current_path
from cutleast_core_lib.core.utilities.process_runner import run_process

from .file import File
from .utils import glob


class Archive:
    """
    Class for accessing all archive files that are supported by 7-zip.
    """

    class _FileStream(RawIOBase):
        def __init__(self, process: subprocess.Popen) -> None:
            self._proc = process
            self._stdout = process.stdout

        @override
        def read(self, size: int = -1) -> bytes:
            assert self._stdout is not None
            return self._stdout.read(size)

        @override
        def readable(self) -> Literal[True]:
            return True

        @override
        def close(self) -> None:
            try:
                if self._stdout:
                    self._stdout.close()
            finally:
                if self._proc:
                    self._proc.wait()

            super().close()

    BIN_PATH: Path = get_current_path() / "res" / "7-zip" / "7z.exe"
    """Path to the 7-zip executable"""

    PATH_KEY: str = "Path"
    """The key for the file path when getting a list of the files."""

    MODIFIED_KEY: str = "Modified"
    """The key for the modified timestamp when getting a list of the files."""

    SIZE_KEY: str = "Size"
    """The key for the size when getting a list of the files."""

    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    """The format of the modified timestamp when getting a list of the files."""

    path: Path
    """The path to the archive file."""

    log: logging.Logger = logging.getLogger("Archive")

    def __init__(self, path: Path) -> None:
        """
        Args:
            path (Path): Path to the archive file.
        """

        self.path = path

    @property
    def files(self) -> list[File]:
        """
        Gets a list of files in the archive.

        Returns:
            list[File]: List of file with relative paths.
        """

        cmd: list[str] = ["7z.exe", "l", "-slt", str(self.path)]
        result: subprocess.CompletedProcess[str] = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )

        entries: list[File] = []
        current: dict[str, Any] = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            if line == "--":
                if Archive.PATH_KEY in current:
                    dt = datetime.datetime.strptime(
                        current[Archive.MODIFIED_KEY], Archive.DATE_FORMAT
                    )
                    ts = int(time.mktime(dt.timetuple()))

                    entries.append(
                        File(
                            path=current[Archive.PATH_KEY],
                            size=current[Archive.SIZE_KEY],
                            last_modified=ts,
                            creation_time=ts,
                        )
                    )
                current = {}
                continue

            if "=" in line:
                key: str
                value: str
                key, value = line.split("=", 1)
                current[key.strip()] = value.strip()

        return entries

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
            str(Archive.BIN_PATH),
            "x" if full_paths else "e",
            str(self.path),
            f"-o{dest}",
            "-aoa",
            "-y",
        ]

        run_process(cmd)

    def extract(self, file: Path, dest: Path, full_paths: bool = True) -> None:
        """
        Extracts a single file.

        Args:
            file (Path): Path of the file to extract.
            dest (Path): Folder to extract file to.
            full_paths (bool, optional):
                Toggles whether path within archives is retained. Defaults to True.

        Raises:
            RuntimeError: When the 7-zip commandline returns a non-zero exit code.
        """

        cmd: list[str] = [
            str(Archive.BIN_PATH),
            "x" if full_paths else "e",
            f"-o{dest}",
            "-aoa",
            "-y",
            "--",
            str(self.path),
            str(file),
        ]

        run_process(cmd)

    def extract_files(
        self, files: list[Path], dest: Path, full_paths: bool = True
    ) -> None:
        """
        Extracts multiple files.

        Args:
            files (list[Path]): List of files to extract.
            dest (Path): Folder to extract files to.
            full_paths (bool, optional):
                Toggles whether paths within archive are retained. Defaults to True.

        Raises:
            RuntimeError: When the 7-zip commandline returns a non-zero exit code.
        """

        if not len(files):
            return

        cmd: list[str] = [
            str(Archive.BIN_PATH),
            "x" if full_paths else "e",
            f"-o{dest}",
            "-aoa",
            "-y",
            str(self.path),
        ]

        # Write filenames to a txt file to workaround commandline length limit
        filenames_txt = self.path.with_suffix(".txt")
        with open(filenames_txt, "w", encoding="utf8") as file:
            file.write("\n".join(str(f) for f in files))
        cmd.append(f"@{filenames_txt}")

        try:
            run_process(cmd)
        finally:
            os.remove(filenames_txt)

    def extract_files_map(
        self,
        files: dict[Path, Path],
        dest: Path,
    ) -> None:
        """
        Extracts multiple files and remaps their archive paths to custom relative
        destination paths.

        Extraction is performed into a temporary directory located on the same drive as
        `dest` to avoid cross-device copies and C:\\ temp usage.

        Args:
            files (dict[Path, Path]):
                Dictionary of archive-internal paths to destination paths, relative to
                `dest`.
            dest (Path): Base directory where files should be placed.

        Raises:
            FileNotFoundError: If an extracted file cannot be located.
            ValueError: If a target path escapes `dest`.
            RuntimeError: When the 7-zip commandline returns a non-zero exit code.
        """

        if not len(files):
            return

        dest = dest.resolve()
        dest.mkdir(parents=True, exist_ok=True)

        tmp_dir: Path = dest.parent / f".__extract_tmp_{uuid.uuid4().hex}"
        tmp_dir.mkdir(parents=True, exist_ok=False)

        cmd: list[str] = [
            str(Archive.BIN_PATH),
            "x",
            str(self.path),
            f"-o{tmp_dir}",
            "-aoa",
            "-y",
        ]

        filenames_txt: Path = self.path.with_suffix(".txt")
        filenames_txt.write_text(
            "\n".join(str(p) for p in files.keys()),
            encoding="utf8",
        )
        cmd.append(f"@{filenames_txt}")

        try:
            run_process(cmd)

            for archive_path, relative_target in files.items():
                src: Path = tmp_dir / archive_path
                if not src.exists():
                    raise FileNotFoundError(f"Extracted file not found: {archive_path}")

                target: Path = (dest / relative_target).resolve()

                # prevent directory traversal
                if not str(target).startswith(str(dest)):
                    raise ValueError(
                        f"Target path escapes destination: {relative_target}"
                    )

                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(src, target)

        finally:
            os.remove(filenames_txt)
            if tmp_dir.is_dir():
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def get_file_stream(self, file: Path) -> BinaryIO:
        """
        Gets an in-memory stream for a file in the archive.

        Args:
            file (Path): Path to the file within the archive.

        Returns:
            BinaryIO: Binary stream.
        """

        cmd: list[str] = [
            str(Archive.BIN_PATH),
            "x",
            str(self.path),
            str(file),
            "-so",  # write extracted file to stdout
            "-y",
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not proc.stdout:
            raise RuntimeError("Failed to open stdout pipe for 7z process.")

        return BufferedReader(Archive._FileStream(proc))

    def glob(self, pattern: str) -> list[Path]:
        """
        Gets a list of file paths that match a specified pattern.

        Args:
            pattern (str): Pattern that matches everything that fnmatch supports

        Returns:
            list[Path]: List of matching file paths, relative to the archive root.
        """

        matches: list[Path] = glob(pattern, [f.path for f in self.files])
        return matches
