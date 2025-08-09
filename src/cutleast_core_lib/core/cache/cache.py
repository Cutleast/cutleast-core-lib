"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import functools
import logging
import os
import pickle
import shutil
import time
from pathlib import Path
from typing import Any, Callable, Optional, ParamSpec, TypeAlias, TypeVar

from semantic_version import Version

from cutleast_core_lib.core.utilities.singleton import Singleton

from .function_cache import FunctionCache

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")
C = TypeVar("C", bound="Cache")

_Undefined = object()
Undefined: TypeAlias = object


class Cache(Singleton):
    """
    Singleton class for application cache.
    """

    path: Path
    """Path to the cache folder."""

    __cache_version_file: Path
    """Path to the file specifying the cache's version."""

    log: logging.Logger = logging.getLogger("Cache")

    def __init__(self, cache_path: Path, app_version: str) -> None:
        """
        Args:
            cache_path (Path): Path to the cache folder.
            app_version (str):
                Application version, used for invalidating caches from older versions.

        Raises:
            RuntimeError: If a cache instance already exists.
        """

        super().__init__()

        self.path = cache_path
        self.__cache_version_file = self.path / "version"

        if self.__cache_version_file.is_file():
            cache_version: str = self.__cache_version_file.read_text().strip()

            if app_version != "development" and (
                Version(cache_version) < Version(app_version)
            ):
                self.clear_caches()
                self.log.info("Cleared caches due to outdated cache version.")

        elif self.path.is_dir() and os.listdir(self.path):
            self.clear_caches()
            self.log.info("Cleared caches due to missing cache version file.")

        self.path.mkdir(parents=True, exist_ok=True)
        self.__cache_version_file.write_text(app_version)

    def clear_caches(self) -> None:
        """
        Clears all caches.
        """

        shutil.rmtree(self.path, ignore_errors=True)
        self.log.info("Caches cleared.")

    @classmethod
    @FunctionCache.cache
    def __read_file(cls, file_path: Path) -> Any:
        with file_path.open("rb") as file:
            return pickle.load(file)

    @classmethod
    def get_from_cache(
        cls,
        cache_file_path: Path,
        max_age: Optional[float] = None,
        default: T | Undefined = _Undefined,
    ) -> Any | T:
        """
        Gets the content of a cache file and deserializes it with pickle.
        The data is only read once and then cached in-memory.

        Args:
            cache_file_path (Path):
                The path to the cache file, relative to the cache folder.
            max_age (Optional[float], optional):
                The maximum age of the cache file in seconds. Defaults to None.
                When specified, the cache file is deleted if it is older than this.
            default (T | Undefined, optional):
                The default value to return if the cache file does not exist. Defaults
                to undefined (raising a `FileNotFoundError`).

        Raises:
            FileNotFoundError:
                When the cache file does not exist and `default` is None.

        Returns:
            Any: The deserialized content of the cache file.
        """

        cache: Optional[Cache] = cls.get_optional()
        if cache is not None:
            cache_file_path = cache.path / cache_file_path

        # Delete existing cache file that got too old
        if (
            cache_file_path.is_file()
            and max_age is not None
            and (time.time() - cache_file_path.stat().st_mtime) > max_age
        ):
            cache_file_path.unlink()
            cls.log.debug(f"Deleted old cache file: {cache_file_path}")

        if not cache_file_path.is_file() and default is not _Undefined:
            return default

        return cls.__read_file(cache_file_path)

    @classmethod
    def save_to_cache(cls, cache_file_path: Path, data: Any) -> None:
        """
        Serializes data with pickle and saves it to a cache file.
        **Does nothing if there is no cache instance.**

        Args:
            cache_file_path (Path):
                The path to the cache file, relative to the cache folder.
            data (Any): The data to serialize and save to the cache file.
        """

        cache: Optional[Cache] = cls.get_optional()
        if cache is None:
            return

        cache_file_path = cache.path / cache_file_path
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_file_path.open("wb") as file:
            pickle.dump(data, file)

    @classmethod
    def persistent_cache(
        cls,
        *,
        cache_subfolder: Optional[Path] = None,
        id_generator: Optional[Callable[..., str]] = None,
        max_age: Optional[float] = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """
        Caches the result of a function in a specified cache folder using pickle.
        Deletes old cache files from the cache folder if `max_age` is specified.

        Args:
            cache_subfolder (Optional[Path]):
                The subfolder within the cache folder to store the cache files.
                Defaults to None.
            id_generator (Optional[Callable[..., str]]):
                A function that generates a unique identifier for the cache file.
                The function is called with the same arguments as the original function.
                Defaults to `Cache.get_func_identifier()`.
            max_age (Optional[float]):
                The maximum age of the cache file in seconds. Defaults to None.

        Returns:
            Callable[P, R]: The wrapped function with caching enabled.
        """

        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                cache_folder: Path
                if cache_subfolder is None:
                    cache_folder = Path("function_cache")
                else:
                    cache_folder = cache_subfolder

                cache_file_name: str
                if id_generator is None:
                    cache_file_name = FunctionCache.get_func_identifier(
                        func, (args, kwargs)
                    )
                else:
                    cache_file_name = id_generator(*args, **kwargs)
                cache_file_path: Path = cache_folder / (cache_file_name + ".cache")

                result: Optional[R] = cls.get_from_cache(
                    cache_file_path, max_age=max_age, default=None
                )

                if result is None:
                    result = func(*args, **kwargs)
                    cls.save_to_cache(cache_file_path, result)
                    cls.log.debug(
                        f"Saved result for function '{func.__qualname__}' in cache."
                    )
                else:
                    cls.log.debug(
                        f"Got cached result for function '{func.__qualname__}'."
                    )

                return result

            return wrapper

        return decorator
