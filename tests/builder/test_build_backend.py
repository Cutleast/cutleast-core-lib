"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest

from cutleast_core_lib.builder.build_backend import BuildBackend


def test_validate_output_accepts_both_executables(tmp_path: Path) -> None:
    """Tests validation of a complete backend output."""

    (tmp_path / "app.exe").touch()
    (tmp_path / "app_cli.exe").touch()

    BuildBackend.validate_output(tmp_path, "app")


@pytest.mark.parametrize("missing_name", ["app.exe", "app_cli.exe"])
def test_validate_output_rejects_missing_executable(
    tmp_path: Path, missing_name: str
) -> None:
    """Tests validation of an incomplete backend output."""

    for name in {"app.exe", "app_cli.exe"} - {missing_name}:
        (tmp_path / name).touch()

    with pytest.raises(RuntimeError, match=missing_name):
        BuildBackend.validate_output(tmp_path, "app")
