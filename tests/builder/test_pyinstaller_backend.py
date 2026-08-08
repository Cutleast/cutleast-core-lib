"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any, Optional, override

import pytest
from pytest import MonkeyPatch
from semantic_version import Version

from cutleast_core_lib.builder.backends import pyinstaller_backend
from cutleast_core_lib.builder.backends.pyinstaller_backend import PyInstallerBackend
from cutleast_core_lib.builder.build_metadata import BuildMetadata


class CustomPyInstallerBackend(PyInstallerBackend):
    """PyInstaller backend with additional test options."""

    @override
    def get_additional_analysis_options(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> dict[str, Any]:
        return {"hiddenimports": ["test_package"]}

    @override
    def get_additional_exe_options(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> dict[str, Any]:
        return {"upx": False}

    @override
    def get_additional_collect_options(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> dict[str, Any]:
        return {"strip": True}


def get_metadata() -> BuildMetadata:
    """Returns build metadata for backend tests."""

    return BuildMetadata(
        display_name="Test App",
        project_version=Version("1.0.0"),
        file_version="1.0.0.0",
        project_author="Cutleast",
        project_license="MIT",
    )


def test_build_creates_shared_analysis_spec(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Tests creation of the shared-analysis dual-executable spec."""

    monkeypatch.chdir(tmp_path)
    main_module: Path = tmp_path / "main.py"
    main_module.touch()
    commands: list[list[str]] = []

    def run_process(command: list[str], live_output: bool = False) -> None:
        commands.append(command)
        dist_root: Path = Path(
            next(
                arg.removeprefix("--distpath=")
                for arg in command
                if arg.startswith("--distpath=")
            )
        )
        output_folder: Path = dist_root / "output"
        output_folder.mkdir(parents=True)
        (output_folder / "app.exe").touch()
        (output_folder / "app_cli.exe").touch()
        (output_folder / "shared.dll").touch()

    monkeypatch.setattr(pyinstaller_backend, "run_process", run_process)
    backend = CustomPyInstallerBackend()

    output_folder: Path = backend.build(
        main_module, "app", Path("app.ico"), get_metadata()
    )
    spec: str = (tmp_path / "main.pyinstaller-build" / "build.spec").read_text(
        encoding="utf8"
    )

    assert (output_folder / "app.exe").is_file()
    assert (output_folder / "app_cli.exe").is_file()
    assert len(commands) == 1
    assert spec.count("Analysis(") == 1
    assert spec.count("EXE(") == 2
    assert spec.count("COLLECT(") == 1
    assert "name='app'" in spec
    assert "name='app_cli'" in spec
    assert "console=False" in spec
    assert "console=True" in spec
    assert "'hiddenimports': ['test_package']" in spec
    assert "'upx': False" in spec
    assert "'strip': True" in spec

    backend.clean(main_module, "app")
    assert not (tmp_path / "main.pyinstaller-build").exists()


def test_build_rejects_protected_options(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Tests that extensions cannot violate the common output contract."""

    class InvalidBackend(PyInstallerBackend):
        @override
        def get_additional_exe_options(
            self,
            main_module: Path,
            exe_stem: str,
            icon_path: Optional[Path],
            metadata: BuildMetadata,
        ) -> dict[str, Any]:
            return {"console": False}

    monkeypatch.chdir(tmp_path)
    main_module: Path = tmp_path / "main.py"
    main_module.touch()

    with pytest.raises(ValueError, match="console"):
        InvalidBackend().build(main_module, "app", None, get_metadata())
