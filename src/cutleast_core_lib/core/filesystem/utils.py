"""
Copyright (c) Cutleast
"""

import hashlib
import os
import re
import shutil
from pathlib import Path

from virtual_glob import InMemoryPath
from virtual_glob import glob as vglob


def create_folder_list(folder: Path) -> list[Path]:
    """
    Creates a list of all files in all subdirectories of a folder.

    Args:
        folder (Path): Folder to get list of files of.

    Returns:
        list[Path]: List of relative file paths from folder and all subdirectories.
    """

    return [item.relative_to(folder) for item in folder.glob("**/*") if item.is_file()]


def get_file_identifier(file_path: os.PathLike) -> str:
    """
    Creates a blake2b hash of the file path and last modification timestamp and returns
    first 8 characters of the hash.

    Args:
        file_path (os.PathLike): Path to file to hash.

    Returns:
        str: First 8 characters of hash.
    """

    mtime = os.path.getmtime(file_path)
    data = f"{file_path}-{mtime}".encode("utf-8")
    digest = hashlib.blake2b(data, digest_size=8).hexdigest()
    return digest[:8]


def clean_fs_name(folder_or_file_name: str) -> str:
    """
    Cleans a folder or file name of illegal characters like ":".

    Args:
        folder_or_file_name (str): File or folder name to clean.

    Returns:
        str: Cleaned file or folder name.
    """

    return re.sub(r'[:<>?*"|]', "", folder_or_file_name)


def safe_copy(
    src: os.PathLike, dst: os.PathLike, *, follow_symlinks: bool = True
) -> os.PathLike | str:
    """
    Safe version of `shutil.copy` which ignores existing files.

    Args:
        src (os.PathLike): Source file.
        dst (os.PathLike): Destination file.
        follow_symlinks (bool, optional): Follow symlinks. Defaults to True.

    Returns:
        os.PathLike | str: Copied file.
    """

    if os.path.exists(dst):
        return dst

    return shutil.copy(src, dst, follow_symlinks=follow_symlinks)


def norm(path: str) -> str:
    """
    Normalizes a path.

    Args:
        path (str): Path to normalize.

    Returns:
        str: Normalized path.
    """

    return path.replace("\\", "/")


def str_glob(pattern: str, files: list[str], case_sensitive: bool = False) -> list[str]:
    """
    Glob function for a list of files as strings.

    Args:
        pattern (str): Glob pattern.
        files (list[str]): List of files.
        case_sensitive (bool, optional): Case sensitive. Defaults to False.

    Returns:
        list[str]: List of matching files.
    """

    file_map: dict[str, str]
    """
    Map of original file names and normalized file names.
    """

    if case_sensitive:
        file_map = {norm(file): file for file in files}
        pattern = norm(pattern)
    else:
        file_map = {norm(file).lower(): file for file in files}
        pattern = norm(pattern).lower()

    fs: InMemoryPath = InMemoryPath.from_list(list(file_map.keys()))
    matches: list[str] = [
        file_map[p.path] for p in vglob(fs, pattern) if p.path in file_map
    ]

    return matches


def glob(pattern: str, files: list[Path], case_sensitive: bool = False) -> list[Path]:
    """
    Glob function for a list of files as paths.

    Args:
        pattern (str): Glob pattern.
        files (list[Path]): List of files.
        case_sensitive (bool, optional): Case sensitive. Defaults to False.

    Returns:
        list[Path]: List of matching files.
    """

    str_result: list[str] = str_glob(pattern, list(map(str, files)), case_sensitive)
    return list(map(Path, str_result))


def open_in_explorer(path: Path) -> None:
    """
    Opens the specified path in the Windows Explorer.
    Opens the parent folder and selects the item if the specified path
    is a file otherwise it just opens the folder.

    Args:
        path (Path): The path to open.
    """

    if path.is_dir():
        os.startfile(path)
    else:
        os.system(f'explorer.exe /select,"{path}"')


def add_suffix(path: Path, suffix: str) -> Path:
    """
    Adds a suffix to the specified path.

    Convenience method for
        `path.with_suffix(path.suffix + suffix)`

    Args:
        path (Path): Path to add suffix to.
        suffix (str): Suffix to add.

    Returns:
        Path: Path with suffix added.
    """

    return path.with_suffix(path.suffix + suffix)
