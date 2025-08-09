"""
Copyright (c) Cutleast
"""

from pathlib import Path

from builder.build_metadata import BuildMetadata
from pyfakefs.fake_filesystem import FakeFilesystem
from semantic_version import Version
from test.base_test import BaseTest


class TestBuildMetadata(BaseTest):
    """
    Tests `builder.build_metadata.BuildMetadata`.
    """

    def test_from_pyproject(self, test_fs: FakeFilesystem, data_folder: Path) -> None:
        """
        Tests `BuildMetadata.from_pyproject()`.
        """

        # given
        project_root: Path = data_folder / "test_project"
        pyproject_file: Path = project_root / "pyproject.toml"

        # when
        metadata: BuildMetadata = BuildMetadata.from_pyproject(pyproject_file)

        # then
        assert metadata.display_name == "A test project for testing the build system"
        assert metadata.project_version == Version("1.0.0-alpha-1")
        assert metadata.file_version == "1.0.0.1"
        assert metadata.project_author == "Cutleast"
        assert metadata.project_license == "Test license"

    def test_from_pyproject_minimal(self, test_fs: FakeFilesystem) -> None:
        """
        Tests `BuildMetadata.from_pyproject()` with a minimal pyproject.toml file.
        """

        # given
        pyproject_file = Path("test") / "pyproject.toml"
        pyproject_file.parent.mkdir()
        pyproject_file.write_text(
            '[project]\nname = "test-project"\nversion = "1.0.0-alpha-1"'
        )

        # when
        metadata: BuildMetadata = BuildMetadata.from_pyproject(pyproject_file)

        # then
        assert metadata.display_name == "test-project"
        assert metadata.project_version == Version("1.0.0-alpha-1")
        assert metadata.file_version == "1.0.0.1"
        assert metadata.project_author is None
        assert metadata.project_license is None
