"""
Copyright (c) Cutleast
"""

from dataclasses import field
from pathlib import Path
from typing import Optional

from pydantic.dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class BuildConfig:
    """
    Dataclass for the build configuration.
    """

    exe_stem: str
    """Stem (name without suffix) of the final executable name (e.g. "SSE-AT")."""

    main_module: Path = Path("main.py")
    """
    Path to the main module (entry point), relative to the source directory (defaults to
    `main.py`).
    """

    src_dir: Path = Path("src")
    """Path to the source directory, relative to the project root (defaults to `src`)."""

    project_root: Path = field(default_factory=Path.cwd)
    """Project root (defaults to the current working directory)."""

    icon_path: Optional[Path] = None
    """Path to icon file relative to project root."""

    ext_resources_json: Optional[Path] = None
    """
    Path to a json file specifying external resources that are copied to the dist folder,
    relative to project root.
    """

    delete_list: list[Path] = field(default_factory=list)
    """List of paths to remove from final bundle."""

    build_dir: Optional[Path] = None
    """Temporary build directory (defaults to `[project root]/build`)."""

    dist_dir: Optional[Path] = None
    """Final distribution directory (defaults to `[project root]/dist/[exe stem]`)."""

    output_archive: Optional[Path] = None
    """
    Final archive path (defaults to `[project root]/dist/[display name] v[version].zip`).
    """
