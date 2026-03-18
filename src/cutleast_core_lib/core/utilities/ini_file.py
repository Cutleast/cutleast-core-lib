"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional, TypeAlias

IniValue: TypeAlias = bool | int | float | str | None
"""
A single typed value stored in an INI file.
"""

IniData: TypeAlias = dict[str, dict[str, IniValue]]
"""
Parsed representation of an INI file.

The outer key is the section name; the inner key is the option name.
Values are resolved to their most specific Python primitive type.
"""


class IniFile:
    """
    Utility class for reading and writing INI files.
    """

    COMMENT_PREFIXES: tuple[str, ...] = (";", "#")
    """Line prefixes that identify a comment line."""

    @staticmethod
    def __parse_value(raw: str) -> IniValue:
        """
        Converts a raw string from the file into a typed `IniValue`.

        Resolution order: `None` -> `bool` -> `int` -> `float` -> `str`.

        Args:
            raw (str): Stripped value string as read from the file.

        Returns:
            IniValue: The most specific matching Python primitive.
        """

        if raw == "":
            return None

        lower: str = raw.lower()
        if lower == "true":
            return True
        if lower == "false":
            return False

        try:
            return int(raw)
        except ValueError:
            pass

        try:
            return float(raw)
        except ValueError:
            pass

        return raw

    @staticmethod
    def __serialize_value(value: IniValue) -> str:
        """
        Converts a typed `IniValue` to its INI string representation.

        Args:
            value (IniValue): The value to serialize.

        Returns:
            str: The string representation to write into the file.
        """

        if value is None:
            return ""

        if isinstance(value, bool):
            return "true" if value else "false"

        return str(value)

    @classmethod
    def load(cls, path: Path) -> IniData:
        """
        Parses an INI file from disk and returns its typed contents.
        Values are resolved to their most specific Python primitive type.

        Args:
            path (Path): Path to the INI file to read.

        Returns:
            IniData: Dictionary mapping section names to their key-value pairs.

        Raises:
            ValueError: If a key-value pair appears before any section header.
        """

        text: str = path.read_text(encoding="utf8").removeprefix("\ufeff")
        data: IniData = {}
        current_section: Optional[str] = None

        for ln, line in enumerate(text.splitlines(), start=1):
            line = line.strip()

            if not line or line.startswith(IniFile.COMMENT_PREFIXES):
                continue

            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                if current_section not in data:
                    data[current_section] = {}

                continue

            if "=" in line:
                if current_section is None:
                    raise ValueError(
                        f"Key-value pair outside any section at line {ln}: '{line}'"
                    )

                key, _, raw_value = line.partition("=")
                value: IniValue = IniFile.__parse_value(raw_value.strip())
                data[current_section][key.strip()] = value
                continue

        return data

    @staticmethod
    def save(path: Path, data: IniData) -> None:
        """
        Serializes `data` and writes it to `path`.

        Args:
            path (Path): Destination path for the INI file.
            data (IniData): Data to serialize.
        """

        lines: list[str] = []
        for section_index, (section, keys) in enumerate(data.items()):
            if section_index > 0:
                lines.append("")

            lines.append(f"[{section}]")

            for key, value in keys.items():
                serialised = IniFile.__serialize_value(value)
                lines.append(f"{key} = {serialised}")

        content = "\n".join(lines) + "\n"
        path.write_text(content, encoding="utf8")
