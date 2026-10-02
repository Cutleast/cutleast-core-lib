"""
Copyright (c) Cutleast
"""

from pathlib import Path

from pytest import MonkeyPatch
from semantic_version import Version

from cutleast_core_lib.builder.backends import pyinstaller_backend
from cutleast_core_lib.builder.backends.pyinstaller_backend import PyInstallerBackend
from cutleast_core_lib.builder.build_metadata import BuildMetadata


def test_build_uses_shared_analysis_for_gui_and_cli(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Tests the shared-analysis dual-executable spec."""

    monkeypatch.chdir(tmp_path)
    main_module: Path = tmp_path / "main.py"
    main_module.touch()

    def run_process(command: list[str], live_output: bool = False) -> None:
        return None

    monkeypatch.setattr(pyinstaller_backend, "run_process", run_process)
    metadata = BuildMetadata(
        display_name="Test App",
        project_version=Version("1.0.0"),
        file_version="1.0.0.0",
        project_author="Cutleast",
        project_license="MIT",
    )

    PyInstallerBackend().build(main_module, "app", None, metadata)
    spec: str = (tmp_path / "main.pyinstaller-build" / "build.spec").read_text(
        encoding="utf8"
    )

    assert spec.count("Analysis(") == 1
    assert spec.count("EXE(") == 2
    assert spec.count("COLLECT(") == 1
    assert "name='app', console=False" in spec
    assert "name='app_cli', console=True" in spec
