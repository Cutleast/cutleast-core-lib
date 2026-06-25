"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.singleton import Singleton

from .coordinator import ProgressCoordinator


class MainProgressCoordinator(ProgressCoordinator, Singleton):
    """
    Singleton object that delegates the progress of primary processes in an app to any
    number of progress displays and update callbacks.
    """

    @override
    def __init__(self, *, replace_existing_instance: bool = False) -> None:
        super().__init__()
        Singleton.__init__(self, replace_existing_instance=replace_existing_instance)


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

    from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
    from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
    from cutleast_core_lib.ui.utilities.ui_mode import UIMode

    from .taskbar import TaskbarProgressDisplay
    from .widget import ProgressWidget

    app = QApplication(sys.argv)
    IconProvider(UIMode.Dark, "#ffffff")

    MainProgressCoordinator()
    window = QWidget()
    vlayout = QVBoxLayout()
    window.setLayout(vlayout)

    widget = ProgressWidget()
    vlayout.addWidget(widget)

    tb_display = TaskbarProgressDisplay(window.winId())

    coordinator = MainProgressCoordinator.get()
    coordinator.add_display(widget)
    coordinator.add_update_callback(tb_display.updateProgress)
    coordinator.updateMainProgress(
        ProgressUpdate(status_text="Doing something important...", value=0, maximum=0)
    )
    for i in range(5):
        coordinator.updateProgress(
            i,
            ProgressUpdate(
                status_text=f"Worker {i}: Doing something else...", value=0, maximum=0
            ),
        )

    window.show()

    sys.exit(app.exec())
