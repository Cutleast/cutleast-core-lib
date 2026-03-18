"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Callable

import pytest
from cutleast_core_lib.core.utilities.ini_file import IniData, IniFile, IniValue
from cutleast_core_lib.test.utils import Utils


class TestIniFile:
    """
    Tests `cutleast_core_lib.core.utilities.ini_file.IniFile`.
    """

    PARSE_VALUE: str = "parse_value"
    """Name of the private `IniFile.parse_value` method."""

    SERIALIZE_VALUE: str = "serialize_value"
    """Name of the private `IniFile.serialize_value` method."""

    @staticmethod
    def parse_value_stub(raw: str) -> IniValue: ...

    @staticmethod
    def serialize_value_stub(value: IniValue) -> str: ...

    @pytest.fixture
    def parse_value(self) -> Callable[[str], IniValue]:
        """Fixture for the private `IniFile.parse_value` method."""

        return Utils.get_private_method(
            IniFile, TestIniFile.PARSE_VALUE, TestIniFile.parse_value_stub
        )

    @pytest.fixture
    def serialize_value(self) -> Callable[[IniValue], str]:
        """Fixture for the private `IniFile.serialize_value` method."""

        return Utils.get_private_method(
            IniFile, TestIniFile.SERIALIZE_VALUE, TestIniFile.serialize_value_stub
        )

    PARSE_TEST_DATA: list[tuple[str, IniValue]] = [
        ("", None),
        ("true", True),
        ("false", False),
        ("True", True),
        ("FALSE", False),
        ("42", 42),
        ("-7", -7),
        ("3.14", 3.14),
        ("-0.5", -0.5),
        ("Skyrim Special Edition", "Skyrim Special Edition"),
    ]

    @pytest.mark.parametrize("raw, expected_value", PARSE_TEST_DATA)
    def test_parse_value(
        self, raw: str, expected_value: IniValue, parse_value: Callable[[str], IniValue]
    ) -> None:
        """
        Tests that an empty string is resolved to None.
        """

        # when
        result: IniValue = parse_value(raw)

        # then
        assert result == expected_value
        assert type(result) is type(expected_value)

    SERIALIZE_TEST_DATA: list[tuple[IniValue, str]] = [
        (None, ""),
        (True, "true"),
        (False, "false"),
        (42, "42"),
        (-7, "-7"),
        (3.14, "3.14"),
        (-0.5, "-0.5"),
        ("Skyrim Special Edition", "Skyrim Special Edition"),
    ]

    @pytest.mark.parametrize("value, expected_raw", SERIALIZE_TEST_DATA)
    def test_serialize_value(
        self,
        value: IniValue,
        expected_raw: str,
        serialize_value: Callable[[IniValue], str],
    ) -> None:
        """
        Tests that an empty string is resolved to None.
        """

        # when
        result: str = serialize_value(value)

        # then
        assert result == expected_raw

    def test_roundtrip(self, tmp_path: Path) -> None:
        """
        Tests that all IniValue types survive a save -> load cycle.
        """

        # given
        data: IniData = {
            "Types": {
                "flag": True,
                "disabled": False,
                "count": 7,
                "scale": 2.5,
                "name": "Skyrim",
                "empty": None,
            },
            "PluginPersistance": {
                "Python%20Proxy\\tryInit": False,
            },
        }
        ini_path: Path = tmp_path / "out.ini"

        # when
        IniFile.save(ini_path, data)
        result: IniData = IniFile.load(ini_path)

        # then
        assert result == data
