"""
Copyright (c) Cutleast
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, override

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

PROJECT_ROOT: Path = Path(__file__).resolve().parent
"""The root directory of the core library project."""

OUTPUT_FILE: Path = PROJECT_ROOT / "src" / "cutleast_core_lib" / "ui" / "resources_rc.py"
"""The generated Python module that registers the core resources."""


class CustomBuildHook(BuildHookInterface):
    """Compiles and ships the core Qt resource module with every distribution."""

    @override
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """
        Compiles resources and makes the generated module part of the distribution.

        Args:
            version (str): The distribution version being built.
            build_data (dict[str, Any]): Hatchling's mutable build configuration.
        """

        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "compile_resources.py")],
            check=True,
        )
        build_data["force_include"][str(OUTPUT_FILE)] = str(
            Path("cutleast_core_lib") / "ui" / "resources_rc.py"
        )
