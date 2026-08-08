"""
Copyright (c) Cutleast
"""

import os
import struct
import subprocess
import sys
from pathlib import Path

import pytest
from semantic_version import Version

from cutleast_core_lib.builder.backends.cx_freeze_backend import CxFreezeBackend
from cutleast_core_lib.builder.backends.nuitka_backend import NuitkaBackend
from cutleast_core_lib.builder.backends.pyinstaller_backend import PyInstallerBackend
from cutleast_core_lib.builder.build_backend import BuildBackend
from cutleast_core_lib.builder.build_metadata import BuildMetadata


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_BACKEND_BUILDS") != "1",
    reason="Real backend builds are only run by the dedicated Windows CI job.",
)


@pytest.mark.parametrize(
    "backend",
    [NuitkaBackend(), PyInstallerBackend(), CxFreezeBackend()],
    ids=["nuitka", "pyinstaller", "cx-freeze"],
)
def test_backend_output_contract(
    backend: BuildBackend, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Builds a minimal application and verifies the dual-executable contract."""

    monkeypatch.chdir(tmp_path)
    main_module: Path = tmp_path / "main.py"
    main_module.write_text('print("backend-smoke-test")\n', encoding="utf8")
    metadata = BuildMetadata(
        display_name="Backend Test",
        project_version=Version("1.0.0"),
        file_version="1.0.0.0",
        project_author="Cutleast",
        project_license="MIT",
    )

    try:
        if isinstance(backend, CxFreezeBackend):
            output_folder = build_cx_freeze_in_subprocess(tmp_path, main_module)
        else:
            output_folder = backend.build(main_module, "app", None, metadata)
        backend.validate_output(output_folder, "app")

        gui_exe: Path = output_folder / "app.exe"
        cli_exe: Path = output_folder / "app_cli.exe"
        assert get_pe_subsystem(gui_exe) == 2
        assert get_pe_subsystem(cli_exe) == 3

        result = subprocess.run(
            [cli_exe],
            cwd=output_folder,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == "backend-smoke-test"
    finally:
        backend.clean(main_module, "app")


def build_cx_freeze_in_subprocess(tmp_path: Path, main_module: Path) -> Path:
    """Runs cx_Freeze outside pytest so its real `__main__` file can be analyzed."""

    driver: Path = tmp_path / "build_driver.py"
    driver.write_text(
        """from pathlib import Path
from semantic_version import Version
from cutleast_core_lib.builder.backends.cx_freeze_backend import CxFreezeBackend
from cutleast_core_lib.builder.build_metadata import BuildMetadata

CxFreezeBackend().build(
    Path('main.py').resolve(),
    'app',
    None,
    BuildMetadata(
        display_name='Backend Test',
        project_version=Version('1.0.0'),
        file_version='1.0.0.0',
        project_author='Cutleast',
        project_license='MIT',
    ),
)
""",
        encoding="utf8",
    )
    subprocess.run([sys.executable, driver], cwd=tmp_path, check=True)

    return tmp_path / f"{main_module.stem}.cx-freeze-build" / "dist"


def get_pe_subsystem(executable: Path) -> int:
    """Reads the Windows subsystem value from a PE executable."""

    with executable.open("rb") as stream:
        stream.seek(0x3C)
        pe_header_offset: int = struct.unpack("<I", stream.read(4))[0]
        stream.seek(pe_header_offset + 24 + 68)
        return struct.unpack("<H", stream.read(2))[0]
