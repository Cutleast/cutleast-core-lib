"""
Copyright (c) Cutleast
"""

import shutil
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, override

from cutleast_core_lib.core.utilities.process_runner import run_process

from ..build_backend import BuildBackend
from ..build_metadata import BuildMetadata


class NuitkaBackend(BuildBackend):
    """
    Nuitka backend implementation.

    **Requires `Nuitka` to be installed in the project's environment!**
    """

    BASE_ARGS: list[str] = [
        sys.executable,
        "-m",
        "nuitka",
        "--msvc=latest",
        "--standalone",
        "--remove-output",
        "--enable-plugin=pyside6",
        "--nofollow-import-to=tkinter",
    ]
    """A list of base arguments passed to Nuitka."""

    class ConsoleMode(Enum):
        """Enum for Nuitka's supported console modes."""

        Disabled = "disable"
        """This disables the console window entirely."""

        Attach = "attach"
        """
        This will attach to an existing console window (if any) but it won't open a new
        one.
        """

        Force = "force"
        """This will create a new console window or use the existing one."""

        Hide = "hide"
        """This will use an existing console window or creates and minimizes one."""

    console_mode: ConsoleMode

    def __init__(self, console_mode: ConsoleMode = ConsoleMode.Hide) -> None:
        """
        Args:
            console_mode (ConsoleMode, optional):
                Console mode that is passed to Nuitka. Defaults to ConsoleMode.Hide.
        """

        super().__init__()

        self.console_mode = console_mode

    def get_additional_args(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> list[str]:
        """
        Method that returns additional commandline arguments passed to Nuitka.
        Override this method in a subclass to add additional arguments.

        Args:
            main_module (Path):
                Path to the main.py file prepared for building. Usually copied to
                `./build/main.py`.
            exe_stem (str):
                Stem (name without suffix) of the name of the final executable (e.g.
                "SSE-AT").
            icon_path (Optional[Path]): Optional path to a .ico file for the executable.
            metadata (BuildMetadata): Extracted metadata from the pyproject.toml.

        Returns:
            list[str]: List of additional commandline arguments.
        """

        return []

    @override
    def build(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> Path:
        cmd = NuitkaBackend.BASE_ARGS
        cmd += self.get_additional_args(main_module, exe_stem, icon_path, metadata)
        cmd += [
            f"--windows-console-mode={self.console_mode.value}",
            f"--company-name={metadata.project_author}",
            f"--copyright={metadata.project_license}",
            f"--product-name={metadata.display_name}",
            f"--file-description={metadata.display_name}",
            f"--file-version={metadata.file_version}",
            f"--product-version={metadata.file_version}",
            f"--output-filename={exe_stem}.exe",
        ]

        if icon_path is not None:
            cmd.append(f"--windows-icon-from-ico={icon_path}")

        cmd.append(str(main_module))
        self.log.info(f"Running Nuitka command: '{' '.join(cmd)}'...")
        run_process(cmd, live_output=True)

        dist_folder = Path(main_module.stem + ".dist")

        if not dist_folder.is_dir():
            raise RuntimeError(
                f"Nuitka failed to create a distribution folder at {dist_folder}"
            )

        return dist_folder

    @override
    def clean(self, main_module: Path, exe_stem: str) -> None:
        build_folder = Path(main_module.stem + ".build")
        dist_folder = Path(main_module.stem + ".dist")

        shutil.rmtree(build_folder, ignore_errors=True)
        shutil.rmtree(dist_folder, ignore_errors=True)

        # Exclude from git in case the deletion fails
        if build_folder.is_dir():
            (build_folder / ".gitignore").write_text("*")
        if dist_folder.is_dir():
            (dist_folder / ".gitignore").write_text("*")
