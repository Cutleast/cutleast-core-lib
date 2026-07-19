"""
Copyright (c) Cutleast
"""

from typing import Any

import jstyleson as json
from PySide6.QtCore import QFile


def read_resource_bytes(path: str) -> bytes:
    """
    Reads the content of the specified resource.

    **Requires a compiled resource module to be imported!**

    Args:
        path (str): Resource path to file to read.

    Raises:
        FileNotFoundError: When the resource does not exist.

    Returns:
        bytes: Content of the resource.
    """

    path = path.replace("\\", "/")
    file = QFile(path)

    if not file.exists():
        raise FileNotFoundError(path)

    if not file.open(QFile.OpenModeFlag.ReadOnly):
        raise FileNotFoundError(file.fileName())

    try:
        content = bytes(file.readAll().data())
    finally:
        file.close()

    return content


def read_resource(name: str, encoding: str = "utf-8") -> str:
    """
    Reads the content of the specified resource.

    **Requires a compiled resource module to be imported!**

    Args:
        name (str): Resource path to file to read.
        encoding (str, optional):
            Encoding to use when reading the resource. Defaults to "utf-8".

    Raises:
        FileNotFoundError: When the resource does not exist.

    Returns:
        str: Content of the resource.
    """

    return read_resource_bytes(name).decode(encoding)


def load_json_resource(name: str) -> Any:
    """
    Loads a resource a and deserializes it.

    **Requires a compiled resource module to be imported!**

    Args:
        name (str): Resource path to file to load.

    Returns:
        Any: Deserialized content of the resource.
    """

    return json.loads(read_resource(name))
