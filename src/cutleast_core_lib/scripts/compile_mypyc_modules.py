"""
Copyright (c) Cutleast

Script to compile marked Python modules using mypyc.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Iterator

from cutleast_core_lib.core.utilities.process_runner import run_process

MARKER: str = "# mypyc"
"""Marker that indicates which modules are to be compiled."""

MAX_LINE: int = 10
"""Maximum number of lines to check for the marker."""

log: logging.Logger = logging.getLogger("MyPyCCompiler")


def find_marked_modules(directory: Path) -> Iterator[Path]:
    """
    Recursively finds all Python modules in a directory that contain a '# mypyc' marker.

    Args:
        directory (Path): Directory to search recursively.

    Yields:
        Path: Path to each Python file that should be compiled.
    """

    for path in directory.rglob("*.py"):
        try:
            with path.open("r", encoding="utf-8") as file:
                for ln, line in enumerate(file):
                    if ln > MAX_LINE:
                        break

                    if line.startswith(MARKER):
                        yield path
                        break

        except (OSError, UnicodeDecodeError):
            # Skip unreadable or binary-like files
            continue


def compile_with_mypyc(module_path: Path) -> None:
    """
    Compiles a single Python module using mypyc.

    Args:
        module_path (Path): Path to the .py module file.
    """

    log.info(f"Compiling '{module_path}'...")

    # mypyc command — outputs the compiled .pyd next to the source file
    cmd = [sys.executable, "-m", "mypyc", str(module_path)]

    run_process(cmd, live_output=True)


def run(args: argparse.Namespace) -> None:
    """
    Executes the compilation process.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """
    base_dir = Path(args.directory).resolve()
    log.info(f"Scanning directory '{base_dir}'...")

    if not base_dir.is_dir():
        log.error(f"'{base_dir}' does not exist!")
        sys.exit(1)

    marked_modules = list(find_marked_modules(base_dir))

    if not marked_modules:
        log.info("No modules marked with '# mypyc' found.")
        return

    log.info(f"Found {len(marked_modules)} marked module(s). Starting compilation...")

    for module in marked_modules:
        try:
            compile_with_mypyc(module)
        except Exception as ex:
            log.error(f"Failed to compile '{module}': {ex}", exc_info=ex)

    log.info("Compilation complete.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compiles all Python modules in a directory marked with '# mypyc' using "
            "mypyc."
        )
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Path to the base directory to search for Python modules.",
    )

    run(parser.parse_args())


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
