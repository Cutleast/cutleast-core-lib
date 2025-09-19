"""
Copyright (c) Cutleast
"""

from pathlib import Path

from requests import Response, get

from ..cache.cache import Cache
from .exceptions import Non200HttpError


@Cache.persistent_cache(
    cache_subfolder=Path("web_cache"),
    id_generator=lambda url: str(hash(url)),
    max_age=60 * 60 * 24,
)
def get_raw_web_content(url: str) -> bytes:
    """
    Fetches raw content from the given URL. The result is cached persistently for 24
    hours.

    Args:
        url (str): URL to fetch content from.

    Raises:
        Non200HttpError: If the status code is not 200.

    Returns:
        bytes: Raw content of the URL.
    """

    return get_raw_web_content_uncached(url)


def get_raw_web_content_uncached(url: str) -> bytes:
    """
    Fetches raw content from the given URL. The result is not cached.

    Args:
        url (str): URL to fetch content from.

    Raises:
        Non200HttpError: If the status code is not 200.

    Returns:
        bytes: Raw content of the URL.
    """

    res: Response = get(url)

    if res.status_code != 200:
        raise Non200HttpError(url, res.status_code)

    return res.content
