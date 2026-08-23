"""
Copyright (c) Cutleast
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
"""The root directory of the core library project."""


def pytest_sessionstart() -> None:
    """Compiles core Qt resources before test modules import the UI package."""

    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "compile_resources.py")],
        check=True,
    )
