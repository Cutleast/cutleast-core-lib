"""
Copyright (c) Cutleast
"""

from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock, current_thread
from typing import Any, Optional, ParamSpec, TypeVar, override

from cutleast_core_lib.ui.widgets.progress_dialog import ProgressDialog

P = ParamSpec("P")
T = TypeVar("T")


class ProgressThreadPoolExecutor(ThreadPoolExecutor):
    """
    A custom ThreadPoolExecutor that displays progress in a ProgressDialog.
    Each worker thread gets its own progress bar that displays the progress
    and status of the task currently processed by that worker.
    The executor displays the total progress (number of tasks completed) in the main
    progress bar.

    **Please note that callables submitted to this executor must accept a progress
    callback function as their first positional argument.**
    """

    __dialog: ProgressDialog
    __lock: Lock
    __completed_tasks: int
    __total_tasks: int

    __main_progress_text: str

    __worker_ids: dict[str, int]
    """Dictionary mapping the thread names to their progress id."""

    def __init__(
        self,
        dialog: ProgressDialog,
        max_workers: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(max_workers=max_workers, *args, **kwargs)

        self.__dialog = dialog
        self.__lock = Lock()
        self.__completed_tasks = 0
        self.__total_tasks = 0
        self.__worker_ids = {}
        self.__main_progress_text = ""

    def set_main_progress_text(self, text: str) -> None:
        self.__main_progress_text = text

    @override
    def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> Future[T]:
        """
        Submits a callable to be executed with the given arguments.

        Schedules the callable to be executed as fn(*args, **kwargs) and returns
        a Future instance representing the execution of the callable.

        **The callable must accept a progress callback function as its first positional
        argument.**

        Args:
            fn (Callable[..., T]): The callable to be executed.

        Returns:
            A Future representing the given call.
        """

        with self.__lock:
            self.__total_tasks += 1

        def worker_fn(*_args: Any, **_kwargs: Any) -> T:
            thread_name: str = current_thread().name

            with self.__lock:
                worker_id: int = self.__worker_ids.setdefault(
                    thread_name, len(self.__worker_ids) + 1
                )

            def update_callback(payload: ProgressDialog.UpdatePayload) -> None:
                self.__dialog.updateProgress(worker_id, payload)

            try:
                result: T = fn(update_callback, *_args, **_kwargs)
                return result

            finally:
                with self.__lock:
                    self.__completed_tasks += 1

                self.__dialog.updateMainProgress(
                    ProgressDialog.UpdatePayload(
                        status_text=(
                            f"{self.__main_progress_text} ({self.__completed_tasks} / "
                            f"{self.__total_tasks})"
                        ),
                        progress_value=self.__completed_tasks,
                        progress_max=self.__total_tasks,
                    )
                )

        return super().submit(worker_fn, *args, **kwargs)


if __name__ == "__main__":
    import random
    import sys
    import time
    from concurrent.futures import as_completed

    from PySide6.QtWidgets import QApplication

    from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
    from cutleast_core_lib.ui.utilities.ui_mode import UIMode

    app = QApplication(sys.argv)
    IconProvider(UIMode.Dark, "#ffffff")

    def example_task(
        update: Callable[[ProgressDialog.UpdatePayload], None], task_id: int
    ) -> None:
        """Simulate a long-running task with progress updates."""

        for i in range(0, 101, 10):
            time.sleep(random.uniform(0.05, 0.2))
            update(
                ProgressDialog.UpdatePayload(
                    progress_value=i,
                    progress_max=100,
                    status_text=f"Processing task {task_id + 1}... ({i} %)",
                )
            )

    def run_parallel(dialog: ProgressDialog[None]) -> None:
        """Executes multiple tasks in parallel using 4 worker threads."""

        dialog.updateMainProgress(
            ProgressDialog.UpdatePayload(
                status_text="Running tasks...",
                progress_value=0,
                progress_max=0,
            )
        )

        with ProgressThreadPoolExecutor(dialog, max_workers=4) as executor:
            executor.set_main_progress_text("Running tasks...")

            futures: list[Future] = []
            for task_id in range(120):
                futures.append(executor.submit(example_task, task_id=task_id))

            for f in as_completed(futures):
                f.result()

    ProgressDialog(run_parallel).run()
