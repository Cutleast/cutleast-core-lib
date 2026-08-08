"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional, override

import pytest
from pytest import MonkeyPatch
from semantic_version import Version

from cutleast_core_lib.builder.backends import nuitka_backend
from cutleast_core_lib.builder.backends.nuitka_backend import NuitkaBackend
from cutleast_core_lib.builder.build_metadata import BuildMetadata


class CustomNuitkaBackend(NuitkaBackend):
    """Nuitka backend with an additional test option."""

    @override
    def get_additional_args(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> list[str]:
        return ["--include-package=test-package"]


def get_metadata() -> BuildMetadata:
    """Returns build metadata for backend tests."""

    return BuildMetadata(
        display_name="Test App",
        project_version=Version("1.0.0"),
        file_version="1.0.0.0",
        project_author="Cutleast",
        project_license="MIT",
    )


def test_build_creates_gui_and_cli_executables(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Tests the common output contract and target-specific Nuitka options."""

    monkeypatch.chdir(tmp_path)
    main_module: Path = tmp_path / "source" / "main.py"
    main_module.parent.mkdir()
    main_module.touch()
    commands: list[list[str]] = []

    def run_process(command: list[str], live_output: bool = False) -> None:
        commands.append(command)
        output_dir: Path = Path(
            next(
                arg.removeprefix("--output-dir=")
                for arg in command
                if arg.startswith("--output-dir=")
            )
        )
        output_name: str = next(
            arg.removeprefix("--output-filename=")
            for arg in command
            if arg.startswith("--output-filename=")
        )
        dist_folder: Path = output_dir / "main.dist"
        dist_folder.mkdir(parents=True)
        (dist_folder / output_name).touch()
        (dist_folder / "shared.dll").touch()

    monkeypatch.setattr(nuitka_backend, "run_process", run_process)
    backend = CustomNuitkaBackend()

    output_folder: Path = backend.build(main_module, "app", None, get_metadata())

    assert (output_folder / "app.exe").is_file()
    assert (output_folder / "app_cli.exe").is_file()
    assert (output_folder / "shared.dll").is_file()
    assert len(commands) == 2
    assert "--windows-console-mode=disable" in commands[0]
    assert "--output-filename=app.exe" in commands[0]
    assert "--windows-console-mode=force" in commands[1]
    assert "--output-filename=app_cli.exe" in commands[1]
    assert all("--include-package=test-package" in command for command in commands)

    backend.clean(main_module, "app")
    assert not (tmp_path / "main.nuitka-build").exists()


def test_build_rejects_different_dependency_layouts(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Tests that only equivalent Nuitka distributions are merged."""

    monkeypatch.chdir(tmp_path)
    main_module: Path = tmp_path / "main.py"
    main_module.touch()

    def run_process(command: list[str], live_output: bool = False) -> None:
        output_dir: Path = Path(
            next(
                arg.removeprefix("--output-dir=")
                for arg in command
                if arg.startswith("--output-dir=")
            )
        )
        output_name: str = next(
            arg.removeprefix("--output-filename=")
            for arg in command
            if arg.startswith("--output-filename=")
        )
        dist_folder: Path = output_dir / "main.dist"
        dist_folder.mkdir(parents=True)
        (dist_folder / output_name).touch()
        if output_name.endswith("_cli.exe"):
            (dist_folder / "cli-only.dll").touch()

    monkeypatch.setattr(nuitka_backend, "run_process", run_process)

    with pytest.raises(RuntimeError, match="different dependency layouts"):
        NuitkaBackend().build(main_module, "app", None, get_metadata())
