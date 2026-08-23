"""
Copyright (c) Cutleast
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
"""The root directory of the core library project."""

RESOURCE_FILE: Path = PROJECT_ROOT / "res" / "resources.qrc"
"""The Qt resource collection to compile."""

OUTPUT_FILE: Path = PROJECT_ROOT / "src" / "cutleast_core_lib" / "ui" / "resources_rc.py"
"""The generated Python module that registers the core resources."""


def compile_resources() -> None:
    """
    Compiles the core Qt resource collection into its importable Python module.

    Raises:
        subprocess.CalledProcessError: When pyside6-rcc fails.
    """

    rcc_executable: Path = Path(sys.executable).with_name("pyside6-rcc.exe")
    subprocess.run(
        [str(rcc_executable), str(RESOURCE_FILE), "-o", str(OUTPUT_FILE)], check=True
    )


if __name__ == "__main__":
    compile_resources()
