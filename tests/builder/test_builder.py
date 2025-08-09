"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional, override

from builder.backends.nuitka_backend import NuitkaBackend
from builder.build_backend import BuildBackend
from builder.build_config import BuildConfig
from builder.build_metadata import BuildMetadata
from builder.builder import Builder
from pyfakefs.fake_filesystem import FakeFilesystem
from semantic_version import Version
from test.base_test import BaseTest
from test.utils import Utils


class TestBuilder(BaseTest):
    """
    Tests `builder.builder.Builder`.
    """

    @staticmethod
    def prepare_src_stub(build_folder: Path) -> Path:
        """
        Stub for `Builder.__prepare_src()`.
        """

        raise NotImplementedError

    @staticmethod
    def load_external_resources_stub() -> dict[Path, Path]:
        """
        Stub for `Builder.__load_external_resources()`.
        """

        raise NotImplementedError

    @staticmethod
    def copy_external_resources_stub() -> None:
        """
        Stub for `Builder.__copy_external_resources()`.
        """

        raise NotImplementedError

    @staticmethod
    def delete_unused_files_stub(dist_folder: Path) -> None:
        """
        Stub for `Builder.__delete_unused_files()`.
        """

        raise NotImplementedError

    @staticmethod
    def archive_dist_stub(dist_folder: Path, output_path: Path) -> None:
        """
        Stub for `Builder.__archive_dist()`.
        """

        raise NotImplementedError

    def test_prepare_src(self, test_fs: FakeFilesystem, data_folder: Path) -> None:
        """
        Tests `Builder.__prepare_src()`.
        """

        # given
        preprocess_calls: list[tuple[Path, BuildMetadata]] = []

        class TestBackend(BuildBackend):
            """
            Test backend.
            """

            @override
            def preprocess_source(
                self, source_folder: Path, metadata: BuildMetadata
            ) -> None:
                preprocess_calls.append((source_folder, metadata))

            @override
            def build(
                self,
                main_module: Path,
                exe_stem: str,
                icon_path: Optional[Path],
                metadata: BuildMetadata,
            ) -> Path:
                raise NotImplementedError

        backend = TestBackend()
        config = BuildConfig(exe_stem="test", project_root=data_folder / "test_project")
        builder = Builder(config, backend)
        build_folder: Path = config.project_root / "build"

        # when
        main_module: Path = Utils.get_private_method(
            builder, "prepare_src", TestBuilder.prepare_src_stub
        )(config.project_root / "build")

        # then
        assert preprocess_calls == [
            (
                build_folder,
                BuildMetadata(
                    display_name="A test project for testing the build system",
                    project_version=Version("1.0.0-alpha-1"),
                    file_version="1.0.0.1",
                    project_author="Cutleast",
                    project_license="Test license",
                ),
            )
        ]
        assert build_folder.is_dir()
        assert main_module == build_folder / "main.py"
        assert (build_folder / "main.py").is_file()

    def test_load_external_resources(self, data_folder: Path) -> None:
        """
        Tests `Builder.__load_external_resources()`.
        """

        # given
        config = BuildConfig(
            exe_stem="test",
            project_root=data_folder / "test_project",
            ext_resources_json=Path("res") / "ext_resources.json",
        )
        builder = Builder(config, NuitkaBackend())

        # when
        ext_resources: dict[Path, Path] = Utils.get_private_method(
            builder, "load_external_resources", TestBuilder.load_external_resources_stub
        )()

        # then
        assert ext_resources == {
            Path("res") / ".." / "LICENSE": Path("res") / ".." / "LICENSE",
            Path("res") / "resources" / "test1.txt": (
                Path("res") / "resources" / "test1.txt"
            ),
            Path("res") / "resources" / "test2.txt": (
                Path("res") / "resources" / "test2.txt"
            ),
            Path("res") / "resources" / "test3.txt": (
                Path("res") / "resources" / "test3.txt"
            ),
            Path("res") / "style.qss": Path("res") / "style.qss",
        }
