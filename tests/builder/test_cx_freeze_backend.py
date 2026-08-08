"""
Copyright (c) Cutleast
"""

import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from pytest import MonkeyPatch
from semantic_version import Version

from cutleast_core_lib.builder.backends.cx_freeze_backend import CxFreezeBackend
from cutleast_core_lib.builder.build_metadata import BuildMetadata


def test_build_creates_gui_and_cli_executables(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Tests the common output contract of the cx_Freeze backend."""

    monkeypatch.chdir(tmp_path)
    main_module: Path = tmp_path / "main.py"
    main_module.touch()
    setup_calls: list[dict[str, Any]] = []
    fake_module = ModuleType("cx_Freeze")

    def executable(*args: object, **kwargs: object) -> dict[str, object]:
        return {"args": args, **kwargs}

    def setup(**kwargs: Any) -> None:
        setup_calls.append(kwargs)
        output_folder = Path(kwargs["options"]["build_exe"]["build_exe"])
        output_folder.mkdir(parents=True)
        for target in kwargs["executables"]:
            (output_folder / target["target_name"]).touch()

    fake_module.Executable = executable  # type: ignore[attr-defined]
    fake_module.setup = setup  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "cx_Freeze", fake_module)
    original_argv: list[str] = sys.argv.copy()
    metadata = BuildMetadata(
        display_name="Test App",
        project_version=Version("1.0.0"),
        file_version="1.0.0.0",
        project_author="Cutleast",
        project_license="MIT",
    )
    backend = CxFreezeBackend()

    output_folder: Path = backend.build(main_module, "app", None, metadata)

    assert (output_folder / "app.exe").is_file()
    assert (output_folder / "app_cli.exe").is_file()
    assert [target["base"] for target in setup_calls[0]["executables"]] == [
        "gui",
        "console",
    ]
    assert setup_calls[0]["script_args"] == ["build_exe"]
    assert sys.argv == original_argv

    backend.clean(main_module, "app")
    assert not (tmp_path / "main.cx-freeze-build").exists()
