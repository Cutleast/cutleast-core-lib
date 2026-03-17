"""
Copyright (c) Cutleast
"""

import hashlib
from typing import BinaryIO, Optional

from cutleast_core_lib.core.multithreading.progress import (
    ProgressUpdate,
    UpdateCallback,
    update,
)


def sha256_hash(data: bytes) -> str:
    """
    Calculates a shortened SHA256 hash of the given data.

    Args:
        data (bytes): Data to hash.

    Returns:
        str: Shortened hash.
    """

    return hashlib.sha256(data).hexdigest()[:8]


def md5_hash_stream(
    stream: BinaryIO,
    size: int,
    chunk_size: int = 1 * 1024 * 1024,
    update_callback: Optional[UpdateCallback] = None,
) -> str:
    """
    Calculates an MD5 hash by reading a stream chunk by chunk.

    Args:
        stream (BinaryIO): Stream to read from.
        size (int): Total size in bytes.
        chunk_size (int, optional): Chunk size. Defaults to 1 MB.
        update_callback (Optional[UpdateCallback], optional):
            Optional update callback. Defaults to None.

    Returns:
        str: MD5 hash.
    """

    hash_md5 = hashlib.md5()

    data_read: int = 0
    while (chunk := stream.read(chunk_size)) != b"":
        hash_md5.update(chunk)
        data_read += len(chunk)
        if size > chunk_size:
            update(update_callback, ProgressUpdate(value=data_read, maximum=size))

    return hash_md5.hexdigest()
