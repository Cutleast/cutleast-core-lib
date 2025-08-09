"""
Copyright (c) Cutleast
"""

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
        cmd = NuitkaBackend.BASE_ARGS
        cmd += self.get_additional_args(main_module, exe_stem, icon_path, metadata)
        cmd += [
            f"--company-name={metadata.project_author}",
            f"--copyright={metadata.project_license}",
            f"--product-name={metadata.display_name}",
            f"--file-description={metadata.display_name}",
            f"--file-version={metadata.file_version}",
            f"--product-version={metadata.project_version}",
            f"--output-filename={exe_stem}.exe",
        ]

        if icon_path is not None:
            cmd.append(f"--windows-icon-from-ico={icon_path}")

        cmd.append(str(main_module))
        self.log.info(f"Running Nuitka command: '{' '.join(cmd)}'...")
        run_process(cmd)

        dist_folder = Path(main_module.stem + ".dist")

        if not dist_folder.is_dir():
            raise RuntimeError(
                f"Nuitka failed to create a distribution folder at {dist_folder}"
            )

        return dist_folder
