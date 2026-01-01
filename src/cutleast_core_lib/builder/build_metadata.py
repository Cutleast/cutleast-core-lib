"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel
from semantic_version import Version


class BuildMetadata(BaseModel, frozen=True, arbitrary_types_allowed=True):
    """
    Dataclass for build metadata, like author, license, version, etc.
    """

    display_name: str
    """
    Display name of the project. This is the name that will be displayed in some places
    on Windows like the Task Manager or the Apps and Features list (when installed with
    something like InnoSetup).
    """

    project_version: Version
    """The full version specifier of the project."""

    file_version: str
    """
    The file version for the executable. Must match the pattern \"?.?.?.?\", e.g.
    \"1.2.3.4\".
    """

    project_author: Optional[str]
    """
    The name of the project's main author. Gets written to the versioninfo's \"Company\"
    field.
    """

    project_license: Optional[str]
    """A copyright notice or the name of the project's license."""

    @staticmethod
    def from_pyproject(project_file: Path) -> BuildMetadata:
        """
        Parses the specified pyproject.toml file and returns the project's metadata.

        Args:
            project_file (Path): The path to the pyproject.toml file.

        Returns:
            BuildMetadata: The project's metadata.
        """

        project_data: dict[str, Any] = tomllib.loads(
            project_file.read_text(encoding="utf8")
        )["project"]
        project_name: str = project_data.get("description", project_data["name"])
        project_version = Version(project_data["version"])

        project_author: Optional[str] = None
        if "authors" in project_data:
            project_author = project_data["authors"][0]["name"]

        project_license: Optional[str] = None
        if "license" in project_data:
            license_file: Path = project_file.parent / project_data["license"]["file"]
            project_license = (
                license_file.read_text(encoding="utf8").splitlines()[0].strip()
            )

        file_version = str(project_version.truncate())
        if project_version.prerelease:
            file_version += "." + project_version.prerelease[0].rsplit("-", 1)[1]

        return BuildMetadata(
            display_name=project_name,
            project_version=project_version,
            file_version=file_version,
            project_author=project_author,
            project_license=project_license,
        )
