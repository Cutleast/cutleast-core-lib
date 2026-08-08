"""
Copyright (c) Cutleast
"""

import pprint
import shutil
import sys
from pathlib import Path
from typing import Any, Optional, override

from cutleast_core_lib.core.utilities.process_runner import run_process

from ..build_backend import BuildBackend
from ..build_metadata import BuildMetadata


class PyInstallerBackend(BuildBackend):
    """
    PyInstaller backend implementation.

    **Requires `PyInstaller` to be installed in the project's environment!**
    """

    def get_additional_analysis_options(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> dict[str, Any]:
        """
        Returns additional options for PyInstaller's `Analysis`.

        Override this method in a subclass to customize module discovery.
        List-valued options get extended, other options get replaced.
        """

        return {}

    def get_additional_exe_options(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> dict[str, Any]:
        """
        Returns additional shared options for both PyInstaller `EXE` targets.

        Contract-specific options such as `name` and `console` cannot be overridden.
        """

        return {}

    def get_additional_collect_options(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> dict[str, Any]:
        """
        Returns additional options for PyInstaller's `COLLECT`.

        The collection name is controlled by the backend and cannot be overridden.
        """

        return {}

    @override
    def build(
        self,
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        metadata: BuildMetadata,
    ) -> Path:
        output_root: Path = Path.cwd() / f"{main_module.stem}.pyinstaller-build"
        shutil.rmtree(output_root, ignore_errors=True)
        output_root.mkdir(parents=True)

        analysis_options: dict[str, Any] = {
            "pathex": [str(main_module.parent)],
            "binaries": [],
            "datas": [],
            "hiddenimports": [],
            "hookspath": [],
            "hooksconfig": {},
            "runtime_hooks": [],
            "excludes": ["tkinter", "unittest"],
            "noarchive": False,
        }
        self.__merge_options(
            analysis_options,
            self.get_additional_analysis_options(
                main_module, exe_stem, icon_path, metadata
            ),
            {"scripts"},
        )

        exe_options: dict[str, Any] = {
            "debug": False,
            "bootloader_ignore_signals": False,
            "strip": False,
            "upx": True,
            "disable_windowed_traceback": False,
        }
        self.__merge_options(
            exe_options,
            self.get_additional_exe_options(main_module, exe_stem, icon_path, metadata),
            {"name", "console", "icon", "exclude_binaries"},
        )

        collect_options: dict[str, Any] = {"strip": False, "upx": True}
        self.__merge_options(
            collect_options,
            self.get_additional_collect_options(
                main_module, exe_stem, icon_path, metadata
            ),
            {"name"},
        )

        spec_path: Path = output_root / "build.spec"
        spec_path.write_text(
            self.__get_spec(
                main_module,
                exe_stem,
                icon_path,
                analysis_options,
                exe_options,
                collect_options,
            ),
            encoding="utf8",
        )

        dist_root: Path = output_root / "dist"
        cmd: list[str] = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            f"--distpath={dist_root}",
            f"--workpath={output_root / 'work'}",
            str(spec_path),
        ]
        self.log.info(f"Running PyInstaller command: '{' '.join(cmd)}'...")
        run_process(cmd, live_output=True)

        return dist_root / "output"

    @staticmethod
    def __merge_options(
        options: dict[str, Any],
        additional_options: dict[str, Any],
        protected_options: set[str],
    ) -> None:
        """Merges backend-specific options while protecting the output contract."""

        invalid_options: set[str] = additional_options.keys() & protected_options
        if invalid_options:
            names: str = ", ".join(sorted(invalid_options))
            raise ValueError(
                f"Cannot override protected PyInstaller option(s): {names}"
            )

        for option, value in additional_options.items():
            if isinstance(value, list):
                options.setdefault(option, []).extend(value)
            else:
                options[option] = value

    @staticmethod
    def __get_spec(
        main_module: Path,
        exe_stem: str,
        icon_path: Optional[Path],
        analysis_options: dict[str, Any],
        exe_options: dict[str, Any],
        collect_options: dict[str, Any],
    ) -> str:
        """Renders the shared-analysis PyInstaller spec."""

        analysis_repr: str = pprint.pformat(
            PyInstallerBackend.__normalize_option(analysis_options), sort_dicts=True
        )
        exe_repr: str = pprint.pformat(
            PyInstallerBackend.__normalize_option(exe_options), sort_dicts=True
        )
        collect_repr: str = pprint.pformat(
            PyInstallerBackend.__normalize_option(collect_options), sort_dicts=True
        )
        icon_repr: str = repr(str(icon_path)) if icon_path is not None else "None"

        return f"""# Generated by cutleast-core-lib.
analysis_options = {analysis_repr}
exe_options = {exe_repr}
collect_options = {collect_repr}

analysis = Analysis([{str(main_module)!r}], **analysis_options)
pyz = PYZ(analysis.pure)

gui_exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name={exe_stem!r},
    console=False,
    icon={icon_repr},
    **exe_options,
)
cli_exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name={f"{exe_stem}_cli"!r},
    console=True,
    icon={icon_repr},
    **exe_options,
)

collection = COLLECT(
    gui_exe,
    cli_exe,
    analysis.binaries,
    analysis.datas,
    name="output",
    **collect_options,
)
"""

    @staticmethod
    def __normalize_option(value: Any) -> Any:
        """Converts paths in PyInstaller options to spec-compatible strings."""

        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {
                key: PyInstallerBackend.__normalize_option(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [PyInstallerBackend.__normalize_option(item) for item in value]
        if isinstance(value, tuple):
            return tuple(PyInstallerBackend.__normalize_option(item) for item in value)

        return value

    @override
    def clean(self, main_module: Path, exe_stem: str) -> None:
        output_root: Path = Path.cwd() / f"{main_module.stem}.pyinstaller-build"
        shutil.rmtree(output_root, ignore_errors=True)
