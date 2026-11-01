"""
Copyright (c) Cutleast
"""

import time
from pathlib import Path

import pytest

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.test.base_test import BaseTest


class TestCache(BaseTest):
    """
    Tests `core.cache.cache.Cache`.
    """

    def test_persistent_cache(self, cache: Cache) -> None:
        """
        Tests the `core.cache.cache.Cache.persistent_cache`-decorator function.
        """

        # given
        cache_file_name: str = "test_cache_file"
        cache_subfolder: Path = Path("test_persistent_cache")
        calls: list[int] = []

        def sum_(x: int, y: int) -> int:
            result: int = x + y
            calls.append(result)
            return result

        @Cache.persistent_cache(
            cache_subfolder=cache_subfolder, id_generator=lambda x, y: cache_file_name
        )
        def test_function(x: int, y: int) -> int:
            return sum_(x, y)

        # when
        result1: int = test_function(1, 2)
        result2: int = test_function(1, 2)

        # then
        assert calls == [3]
        assert result1 == result2 == 3
        assert (cache.path / cache_subfolder / (cache_file_name + ".cache")).is_file()

        # when
        cache.clear_caches()

        # then
        assert not cache.path.is_dir()

        # when
        result3: int = test_function(1, 2)

        # then
        assert calls == [3, 3]
        assert result3 == 3
        assert (cache.path / cache_subfolder / (cache_file_name + ".cache")).is_file()

    def test_persistence_cache_with_max_age(self, cache: Cache) -> None:
        """
        Tests the `core.cache.cache.Cache.persistent_cache`-decorator function with a
        `max_age` parameter.
        """

        # given
        cache_file_name: str = "test_cache_file"
        cache_subfolder: Path = Path("test_cache_with_max_age")
        calls: list[int] = []

        def sum_(x: int, y: int) -> int:
            result: int = x + y
            calls.append(result)
            return result

        @Cache.persistent_cache(
            cache_subfolder=cache_subfolder,
            id_generator=lambda x, y: cache_file_name,
            max_age=1,
        )
        def test_function(x: int, y: int) -> int:
            return sum_(x, y)

        # when
        result1: int = test_function(1, 2)
        time.sleep(1)
        result2: int = test_function(1, 2)
        result3: int = test_function(1, 2)

        # then
        assert calls == [3, 3]
        assert result1 == result2 == result3 == 3
        assert (cache.path / cache_subfolder / (cache_file_name + ".cache")).is_file()

    def test_multi_instantiation_raises_exception(self, cache: Cache) -> None:
        """
        Tests that instantiating multiple `Cache` instances raises an exception.
        """

        with pytest.raises(RuntimeError, match="Cache is already initialized!"):
            Cache(Path("test_cache"), "development")

    def test_overwritten_cache_file_returns_new_data(self, cache: Cache) -> None:
        """
        Tests that reading a cache file after overwriting it returns the new data, even
        if the file was read before.
        """

        # given
        cache_file_path = Path("test_overwrite") / "entry.cache"
        Cache.save_to_cache(cache_file_path, "old")
        Cache.get_from_cache(cache_file_path)

        # when
        Cache.save_to_cache(cache_file_path, "new")

        # then
        assert Cache.get_from_cache(cache_file_path) == "new"
