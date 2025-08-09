"""
Copyright (c) Cutleast
"""

import logging
import shutil
import time
from pathlib import Path

import jstyleson as json

from .build_backend import BuildBackend
from .build_config import BuildConfig
from .build_metadata import BuildMetadata


class Builder:
    """
    Builder that runs the full build process end-to-end.
    """

    log: logging.Logger = logging.getLogger("Builder")

    config: BuildConfig
    backend: BuildBackend
    metadata: BuildMetadata

    BASE_RES: dict[Path, Path] = {
        Path(__file__).parent.parent / "res" / "path_limit.reg": (
            Path("res") / "path_limit.reg"
        ),
        Path(__file__).parent.parent / "res" / "TaskbarLib.tlb": (
            Path("res") / "TaskbarLib.tlb"
        ),
    }

    def __init__(self, config: BuildConfig, backend: BuildBackend) -> None:
        """
        Args:
            config (BuildConfig): Build configuration.
            backend (BuildBackend): Backend implementation that creates the executable.
        """

        self.config = config
        self.backend = backend
        self.metadata = BuildMetadata.from_pyproject(
            self.config.project_root / "pyproject.toml"
        )

    def __prepare_src(self, build_folder: Path) -> Path:
        """
        Prepares the source code by copying it to the temporary build directory and
        running the backend's preprocessing method.

        Args:
            build_folder (Path): Path to the temporary build directory.

        Returns:
            Path: Path to the main module in the temp build folder.
        """

        if build_folder.is_dir():
            shutil.rmtree(build_folder)
            self.log.warning(f"Deleted existing '{build_folder}'.")

        self.log.info(f"Copying source code to '{build_folder}'...")
        shutil.copytree(self.config.project_root / self.config.src_dir, build_folder)

        main_module: Path = build_folder / self.config.main_module
        self.log.info("Preprocessing source...")
        self.backend.preprocess_source(build_folder, self.metadata)

        return main_module

    def __load_external_resources(self) -> dict[Path, Path]:
        """
        Loads the external resources from the configured JSON file, if any.

        Returns:
            dict[Path, Path]:
                Dictionary of source (relative to the project's root) and destination
                paths (relative to the dist folder).
        """

        if self.config.ext_resources_json is None:
            return {}

        ext_res_file: Path = self.config.project_root / self.config.ext_resources_json
        res_folder: Path = ext_res_file.parent
        raw_resources: list[str] = json.loads(ext_res_file.read_text("utf8"))
        external_resources: dict[Path, Path] = {
            i.relative_to(self.config.project_root): (
                res_folder.relative_to(self.config.project_root)
                / i.relative_to(res_folder)
            )
            for item in raw_resources
            for i in res_folder.glob(item)
        }

        self.log.info(
            f"Got {len(external_resources)} external resource files from "
            f"'{self.config.ext_resources_json}'."
        )

        return external_resources

    def __copy_external_resources(
        self, files: dict[Path, Path], dist_folder: Path
    ) -> None:
        """
        Copies the external resources to the dist folder.

        Args:
            files (dict[Path, Path]):
                Dictionary of source (relative to the project's root) and destination
                paths (relative to the dist folder).
            dist_folder (Path): Path to the dist folder.
        """

        for file, dst in files.items():
            src: Path = self.config.project_root / file
            dst: Path = dist_folder / dst
            self.log.info(f"Copying '{src}' to '{dst}'...")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)

        self.log.info(
            f"Copied {len(files)} external resource files to '{dist_folder}'."
        )

    def __delete_unused_files(self, dist_folder: Path) -> None:
        """
        Deletes configured unused files from the dist folder.

        Args:
            dist_folder (Path): Path to the dist folder.
        """

        for file in self.config.delete_list:
            file: Path = dist_folder / file
            if file.is_file():
                file.unlink()
                self.log.info(f"Deleted '{file}'.")

        self.log.info(
            f"Deleted {len(self.config.delete_list)} unused files from '{dist_folder}'."
        )

    def __archive_dist(self, dist_folder: Path, output_path: Path) -> None:
        """
        Creates a ZIP archive of the dist folder at the specified path.

        Args:
            dist_folder (Path): Path to the dist folder.
            output_path (Path): Path to the output ZIP file.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.is_file():
            output_path.unlink()
            self.log.warning(f"Deleted existing '{output_path}'.")

        shutil.make_archive(
            base_name=str(output_path.with_suffix("")),
            format="zip",
            root_dir=dist_folder.parent,
            base_dir=dist_folder,
        )
        self.log.info(f"Created archive from '{dist_folder}' at '{output_path}'.")

    def run(self) -> Path:
        """
        Runs the entire build process.

        Returns:
            Path: Path to the output ZIP file.
        """

        start: float = time.time()

        self.log.info(
            f"Building {self.metadata.display_name} v{self.metadata.project_version}..."
        )

        build_folder: Path = self.config.project_root / "build"
        if self.config.build_dir is not None:
            build_folder = self.config.build_dir

        self.log.info(f"Preparing source in '{build_folder}'...")
        main_module: Path = self.__prepare_src(build_folder)

        try:
            self.log.info("Running build backend...")
            backend_output: Path = self.backend.build(
                main_module=main_module,
                exe_stem=self.config.exe_stem,
                icon_path=self.config.icon_path,
                metadata=self.metadata,
            )

            dist_folder: Path = self.config.project_root / "dist" / self.config.exe_stem
            if self.config.dist_dir is not None:
                dist_folder = self.config.dist_dir

            if dist_folder.is_dir():
                shutil.rmtree(dist_folder)
                self.log.warning(f"Deleted existing '{dist_folder}'.")

            self.log.info(f"Copying '{backend_output}' to '{dist_folder}'...")
            shutil.copytree(backend_output, dist_folder)

            external_resources: dict[Path, Path] = (
                Builder.BASE_RES | self.__load_external_resources()
            )

            self.log.info("Finalizing build...")
            self.__copy_external_resources(external_resources, dist_folder)
            self.__delete_unused_files(dist_folder)

            output_archive: Path = (
                self.config.project_root
                / "dist"
                / f"{self.metadata.display_name}_v{self.metadata.project_version}.zip"
            )
            if self.config.output_archive is not None:
                output_archive = self.config.output_archive

            self.__archive_dist(dist_folder, output_archive)

            self.log.info(
                f"Build completed successfully in {time.time() - start:.2f} second(s)."
            )

        finally:
            shutil.rmtree(build_folder, ignore_errors=True)
            self.backend.clean(main_module, self.config.exe_stem)
            self.log.info("Cleaned build backend output.")

        return output_archive
