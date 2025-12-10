"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import NoReturn

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from cutleast_core_lib.core.filesystem.file import File
from cutleast_core_lib.core.filesystem.scanner import DirectoryScanner
from cutleast_core_lib.test.base_test import BaseTest


class TestDirectoryScanner(BaseTest):
    """
    Tests for `core.filesystem.scanner.DirectoryScanner`.
    """

    def test_scan_folder_non_recursive(self, test_fs: FakeFilesystem) -> None:
        """
        Tests that scan_folder returns only files in the given folder when
        `recursive=False`.
        """

        # given
        base = Path("C:/data")
        base.mkdir(parents=True)
        a_file: Path = base / "a.txt"
        a_file.write_text("abc")
        b_file: Path = base / "b.bin"
        b_file.write_text("1234")

        sub: Path = base / "sub"
        sub.mkdir(parents=True)
        (sub / "hidden.txt").write_text("ignored")

        # when
        result: list[File] = DirectoryScanner.scan_folder(base, recursive=False)
        paths: set[Path] = {f.path for f in result}

        # then
        assert len(result) == 2
        assert paths == {a_file, b_file}
        assert all(isinstance(f, File) for f in result)

    def test_scan_folder_recursive(self, test_fs: FakeFilesystem) -> None:
        """
        Tests that recursive scanning includes subfolders.
        """

        # given
        base = Path("C:/root")
        base.mkdir(parents=True)
        top_file: Path = base / "top.txt"
        top_file.write_text("1")

        nested: Path = base / "nested"
        nested.mkdir(parents=True)
        deep_file: Path = nested / "deep.txt"
        deep_file.write_text("2")

        # when
        result: list[File] = DirectoryScanner.scan_folder(base)
        paths: set[Path] = {f.path for f in result}

        # then
        assert len(paths) == 2
        assert top_file in paths
        assert deep_file in paths

    def test_scan_folder_propagates_error(
        self, test_fs: FakeFilesystem, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Tests that `ignore_errors=False` propagates exceptions.
        """

        # given
        base = Path("C:/err")
        base.mkdir(parents=True)
        (base / "fail.txt").write_text("hi")

        def broken_scandir(path: Path) -> NoReturn:
            raise PermissionError("Denied")

        monkeypatch.setattr("os.scandir", broken_scandir)

        # when/then
        with pytest.raises(PermissionError):
            DirectoryScanner.scan_folder(base, ignore_errors=False)

    def test_glob_folder_case_insensitive_windows(
        self, test_fs: FakeFilesystem
    ) -> None:
        """
        Tests that `glob_folder` works case-insensitively on Windows (nt).
        """

        # given
        base = Path("C:/glob")
        base.mkdir(parents=True)
        text1_file: Path = base / "text1.TXT"
        text1_file.write_text("x")
        text2_file: Path = base / "text2.txt"
        text2_file.write_text("y")
        (base / "image.PNG").write_text("z")

        # when
        result: list[File] = DirectoryScanner.glob_folder(base, pattern="*.txt")
        paths: set[Path] = {f.path for f in result}

        # then
        assert len(paths) == 2
        assert text1_file in paths
        assert text2_file in paths

    def test_get_folder_size(self, test_fs: FakeFilesystem) -> None:
        """
        Tests that `get_folder_size` returns the sum of file sizes.
        """

        # given
        base = Path("C:/size")
        base.mkdir(parents=True)
        (base / "a.bin").write_text("abcd")  # size 4
        (base / "b.bin").write_text("123456")  # size 6

        # when
        total: int = DirectoryScanner.get_folder_size(base)

        # then
        assert total == 10
