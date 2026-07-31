"""
Copyright (c) Cutleast
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

log: logging.Logger = logging.getLogger("ProcessRunner")

MAX_ERROR_OUTPUT_LENGTH: int = 4_000


def run_process(
    command: list[str], live_output: bool = False, cwd: Optional[Path] = None
) -> None:
    """
    Executes an external command and logs its output in case of an error.

    Args:
        command (list[str]): Executable + arguments to run.
        live_output (bool, optional):
            Whether to print the stdout output in realtime. Defaults to False.
        cwd (Optional[Path], optional):
            The working directory to run the command in. Defaults to None.

    Raises:
        RuntimeError: When the process returns a non-zero exit code.
    """

    output: str = ""

    with subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE if not live_output else sys.stdout,
        stderr=subprocess.PIPE if not live_output else sys.stderr,
        cwd=cwd,
        text=True,
        encoding="utf8",
        errors="ignore",
    ) as process:
        if process.stderr is not None:
            output = process.stderr.read()

    if process.returncode:
        executable_name: str = Path(command[0]).name if command else "<unknown>"
        error_output: str = output.strip()
        if len(error_output) > MAX_ERROR_OUTPUT_LENGTH:
            error_output = error_output[:MAX_ERROR_OUTPUT_LENGTH] + "\n... (truncated)"

        log.error(
            f"Process '{executable_name}' failed with exit code {process.returncode}."
        )
        if error_output:
            log.debug(f"Process stderr:\n{error_output}")
        raise RuntimeError(f"Process returned non-zero exit code: {process.returncode}")
