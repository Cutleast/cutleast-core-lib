"""
Copyright (c) Cutleast
"""

import shutil
import sys
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
        "--assume-yes-for-downloads",
    ]
    """A list of base arguments passed to Nuitka."""

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
        output_root: Path = Path.cwd() / f"{main_module.stem}.nuitka-build"
        shutil.rmtree(output_root, ignore_errors=True)

        gui_dist: Path = self.__build_target(
            main_module,
            exe_stem,
            "disable",
            output_root / "gui",
            icon_path,
            metadata,
        )
        cli_dist: Path = self.__build_target(
            main_module,
            f"{exe_stem}_cli",
            "force",
            output_root / "cli",
            icon_path,
            metadata,
        )
        shutil.copy2(cli_dist / f"{exe_stem}_cli.exe", gui_dist)

        return gui_dist

    def __build_target(
        self,
        main_module: Path,
        target_stem: str,
        console_mode: str,
        output_dir: Path,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> Path:
        """Builds one Nuitka executable target."""

        cmd: list[str] = [
            *NuitkaBackend.BASE_ARGS,
            *self.get_additional_args(main_module, target_stem, icon_path, metadata),
            f"--windows-console-mode={console_mode}",
            f"--company-name={metadata.project_author}",
            f"--copyright={metadata.project_license}",
            f"--product-name={metadata.display_name}",
            f"--file-description={metadata.display_name}",
            f"--file-version={metadata.file_version}",
            f"--product-version={metadata.file_version}",
            f"--output-filename={target_stem}.exe",
            f"--output-dir={output_dir}",
        ]

        if icon_path is not None:
            cmd.append(f"--windows-icon-from-ico={icon_path}")

        cmd.append(str(main_module))
        self.log.info(f"Running Nuitka command: '{' '.join(cmd)}'...")
        run_process(cmd, live_output=True)

        dist_folder: Path = output_dir / f"{main_module.stem}.dist"
        if not (dist_folder / f"{target_stem}.exe").is_file():
            raise RuntimeError(
                f"Nuitka failed to create '{target_stem}.exe' in '{dist_folder}'."
            )

        return dist_folder

    @override
    def clean(self, main_module: Path, exe_stem: str) -> None:
        shutil.rmtree(
            Path.cwd() / f"{main_module.stem}.nuitka-build", ignore_errors=True
        )
