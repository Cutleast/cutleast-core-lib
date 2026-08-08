"""
Copyright (c) Cutleast
"""

from pathlib import Path

from pytest import MonkeyPatch
from semantic_version import Version

from cutleast_core_lib.builder.backends import nuitka_backend
from cutleast_core_lib.builder.backends.nuitka_backend import NuitkaBackend
from cutleast_core_lib.builder.build_metadata import BuildMetadata


def test_build_creates_gui_and_cli_executables(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Tests the shared distribution and target-specific console modes."""

    monkeypatch.chdir(tmp_path)
    main_module: Path = tmp_path / "main.py"
    main_module.touch()
    commands: list[list[str]] = []

    def run_process(command: list[str], live_output: bool = False) -> None:
        commands.append(command)
        output_dir: Path = Path(
            next(arg.split("=", 1)[1] for arg in command if "--output-dir=" in arg)
        )
        output_name: str = next(
            arg.split("=", 1)[1] for arg in command if "--output-filename=" in arg
        )
        dist_folder: Path = output_dir / "main.dist"
        dist_folder.mkdir(parents=True)
        (dist_folder / output_name).touch()

    monkeypatch.setattr(nuitka_backend, "run_process", run_process)
    metadata = BuildMetadata(
        display_name="Test App",
        project_version=Version("1.0.0"),
        file_version="1.0.0.0",
        project_author="Cutleast",
        project_license="MIT",
    )

    output_folder: Path = NuitkaBackend().build(main_module, "app", None, metadata)

    assert (output_folder / "app.exe").is_file()
    assert (output_folder / "app_cli.exe").is_file()
    assert "--windows-console-mode=disable" in commands[0]
    assert "--windows-console-mode=force" in commands[1]
