"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path
from typing import TypeVar

from cutleast_core_lib.core.filesystem.utils import get_file_identifier, str_glob

T = TypeVar("T")


class TestFilesystemUtils:
    """
    Tests `core.filesystem.utils`.
    """

    @staticmethod
    def compare_lists(list1: list[T], list2: list[T]) -> bool:
        """
        Compares two lists and checks if they contain the same elements.

        Args:
            list1 (list[T]): The first list
            list2 (list[T]): The second list

        Returns:
            bool: `True` if the lists are equal, `False` otherwise
        """

        return set(list1) == set(list2)

    def test_glob_flat(self) -> None:
        """
        Tests `glob()` with a flat list.
        """

        # given
        pattern: str = "*.txt"
        files: list[str] = ["a.txt", "b.txt", "c.png"]
        expected_output: list[str] = ["a.txt", "b.txt"]

        # when
        real_output: list[str] = str_glob(pattern, files)

        # then
        assert TestFilesystemUtils.compare_lists(real_output, expected_output)

    def test_glob_nested(self) -> None:
        """
        Tests `glob()` with a single-level folder structure.
        """

        # given
        pattern: str = "*/*.txt"
        files: list[str] = ["a/b.txt", "c/d.png", "e/f.txt"]
        expected_output: list[str] = ["a/b.txt", "e/f.txt"]

        # when
        real_output: list[str] = str_glob(pattern, files)

        # then
        assert TestFilesystemUtils.compare_lists(real_output, expected_output)

    def test_glob_deep(self) -> None:
        """
        Tests `glob()` with a deep folder structure.
        """

        # given
        pattern: str = "**/*.txt"
        files: list[str] = ["a/b/c/d/e/f.txt", "g/h/i/j/k/l/m.txt", "n/o/p/q/r/s/t.png"]
        expected_output: list[str] = ["a/b/c/d/e/f.txt", "g/h/i/j/k/l/m.txt"]

        # when
        real_output: list[str] = str_glob(pattern, files)

        # then
        assert TestFilesystemUtils.compare_lists(real_output, expected_output)

    def test_get_file_identifier_is_stable(self, tmp_path: Path) -> None:
        """
        Tests that `get_file_identifier()` returns the same full-length identifier for
        an unchanged file.
        """

        # given
        file_path: Path = tmp_path / "file.txt"
        file_path.write_text("content", encoding="utf-8")

        # when
        first_identifier: str = get_file_identifier(file_path)
        second_identifier: str = get_file_identifier(file_path)

        # then
        assert first_identifier == second_identifier
        assert len(first_identifier) == 16

    def test_get_file_identifier_includes_size(self, tmp_path: Path) -> None:
        """
        Tests that `get_file_identifier()` changes when the size of a file changes
        while its modification timestamp stays the same.
        """

        # given
        file_path: Path = tmp_path / "file.txt"
        file_path.write_text("content", encoding="utf-8")
        stat: os.stat_result = file_path.stat()
        original_identifier: str = get_file_identifier(file_path)

        # when
        file_path.write_text("different content", encoding="utf-8")
        os.utime(file_path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        changed_identifier: str = get_file_identifier(file_path)

        # then
        assert file_path.stat().st_mtime_ns == stat.st_mtime_ns
        assert changed_identifier != original_identifier

    def test_get_file_identifier_includes_mtime(self, tmp_path: Path) -> None:
        """
        Tests that `get_file_identifier()` changes when the modification timestamp of a
        file changes while its size stays the same.
        """

        # given
        file_path: Path = tmp_path / "file.txt"
        file_path.write_text("content", encoding="utf-8")
        stat: os.stat_result = file_path.stat()
        original_identifier: str = get_file_identifier(file_path)

        # when
        os.utime(file_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
        changed_identifier: str = get_file_identifier(file_path)

        # then
        assert changed_identifier != original_identifier
