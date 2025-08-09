"""
Copyright (c) Cutleast
"""

import sys
from pathlib import Path
from typing import Any, override

from ..build_backend import BuildBackend
from ..build_metadata import BuildMetadata


class CxFreezeBackend(BuildBackend):
    """
    cx_Freeze backend implementation.

    **Requires `cx_Freeze` to be installed in the project's environment!**
    """

    def get_additional_build_options(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Path | None,
        metadata: BuildMetadata,
    ) -> dict[str, Any]:
        """
        Method that returns additional build options passed to cx_Freeze.
        Attributes like `packages`, `includes`, `excludes` get merged.

        Override this method in a subclass to add additional options.

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
            dict[str, Any]: Additional build options.
        """

        return {}

    @override
    def build(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Path | None,
        metadata: BuildMetadata,
    ) -> Path:
        from cx_Freeze import Executable, setup  # pyright: ignore[reportMissingImports]

        outpath: Path = Path.cwd() / f"{exe_stem}.dist"
        build_options: dict[str, Any] = {
            "replace_paths": [("*", "")],
            "include_files": [],
            "include_path": str(main_module.parent),
            "packages": ["ctypes"],
            "includes": ["ctypes.wintypes"],
            "excludes": ["tkinter", "unittest"],
            "zip_include_packages": ["encodings", "PySide6", "shiboken6"],
            "build_exe": str(outpath),
        }

        # Merge additional build options
        for option, additional_option in self.get_additional_build_options(
            main_module, exe_stem, icon_path, metadata
        ).items():
            if isinstance(additional_option, list):
                build_options.setdefault(option, []).extend(additional_option)
            else:
                build_options[option] = additional_option

        executables: list[Executable] = [
            Executable(
                main_module,
                base="gui",
                target_name=f"{exe_stem}.exe",
                icon=icon_path,
                copyright=metadata.project_license,
            ),
            Executable(
                main_module,
                base="console",
                target_name=f"{exe_stem}_cli.exe",
                icon=icon_path,
                copyright=metadata.project_license,
            ),
        ]

        if "build_exe" not in sys.argv:
            sys.argv.append("build_exe")

        setup(
            name=metadata.display_name,
            version=metadata.file_version,
            description=metadata.display_name,
            author=metadata.project_author,
            license=metadata.project_license,
            options={"build_exe": build_options},
            executables=executables,
        )

        return outpath
