"""
Copyright (c) Cutleast
"""

import logging
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Optional

from .build_metadata import BuildMetadata


class BuildBackend(metaclass=ABCMeta):
    """
    Abstract build backend.

    Concrete backends (Nuitka/PyInstaller/cx_Freeze) must implement `build`.
    The builder will call the `build`-method with minimal inputs and expects back
    the folder where the GUI executable, CLI executable and shared dependencies live.
    """

    log: logging.Logger

    def __init__(self) -> None:  # noqa: D107
        self.log = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def validate_output(output_folder: Path, exe_stem: str) -> None:
        """
        Validates the common backend output contract.

        Args:
            output_folder (Path): Folder returned by the backend.
            exe_stem (str): Configured executable stem.

        Raises:
            RuntimeError: If the output folder or one of the executables is missing.
        """

        expected_files: list[Path] = [
            output_folder / f"{exe_stem}.exe",
            output_folder / f"{exe_stem}_cli.exe",
        ]
        missing_files: list[Path] = [
            file for file in expected_files if not file.is_file()
        ]

        if missing_files:
            missing_names: str = ", ".join(file.name for file in missing_files)
            raise RuntimeError(
                f"Build backend failed to create required executable(s) in "
                f"'{output_folder}': {missing_names}"
            )

    def preprocess_source(self, source_folder: Path, metadata: BuildMetadata) -> None:
        """
        Optional pre-processing method that is called before the `build`-method.
        An example use case would be to inject the project version into the app module.
        The default implementation does nothing.

        Args:
            source_folder (Path):
                Path to the temp build folder with the copied source code.
            metadata (BuildMetadata): Extracted metadata from the pyproject.toml.
        """

    @abstractmethod
    def build(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> Path:
        """
        Builds the executable(s).

        Args:
            main_module (Path):
                Path to the main.py file prepared for building. Usually copied to
                `./build/main.py`.
            exe_stem (str):
                Stem (name without suffix) of the name of the final executable (e.g.
                "SSE-AT").
            icon_path (Optional[Path]): Optional path to a .ico file for the executable.
            metadata (BuildMetadata): Extracted metadata from the pyproject.toml.

        Raises:
            RuntimeError: When the build fails.

        Returns:
            Path:
                Path to the folder with the GUI executable, CLI executable and shared
                dependencies.
        """

    @abstractmethod
    def clean(self, main_module: Path, exe_stem: str) -> None:
        """
        Cleans the backend's output folder(s).

        Args:
            main_module (Path): Path to the built main.py.
            exe_stem (str):
                Stem (name without suffix) of the name of the final executable (e.g.
                "SSE-AT").
        """
