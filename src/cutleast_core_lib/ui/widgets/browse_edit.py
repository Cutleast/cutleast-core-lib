"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton

from ..utilities.icon_provider import IconProvider


class BrowseLineEdit(QLineEdit):
    """
    Custom QLineEdit with a "Browse" button to open a QFileDialog.
    """

    __base_path: Optional[Path]
    __browse_button: QPushButton
    __file_mode: QFileDialog.FileMode = QFileDialog.FileMode.AnyFile
    __filters: Optional[list[str]] = None

    pathChanged = Signal(Path, Path)
    """
    This signal gets emitted when a file is selected in the QFileDialog.
    It emits the current path and the selected file.

    Args:
        Path: Current path
        Path: New path
    """

    def __init__(
        self,
        initial_path: Optional[Path] = None,
        base_path: Optional[Path] = None,
        *args: Any,
        **kwargs: dict[str, Any],
    ) -> None:
        """
        Args:
            initial_path (Optional[Path], optional):
                Initial path to display. Defaults to None.
            base_path (Optional[Path], optional):
                Base path for relative paths. Defaults to None.
        """

        super().__init__(*args, **kwargs)

        self.__base_path = base_path

        self.__init_ui()

        if initial_path is not None:
            self.setPath(initial_path)

    def __init_ui(self) -> None:
        hlayout: QHBoxLayout = QHBoxLayout(self)
        hlayout.setContentsMargins(0, 0, 0, 0)

        # Push Browse Button to the right-hand side
        hlayout.addStretch()

        self.__browse_button = QPushButton()
        self.__browse_button.setIcon(IconProvider.get_qta_icon("fa5s.folder-open"))
        self.__browse_button.clicked.connect(self.__browse)
        self.__browse_button.setCursor(Qt.CursorShape.ArrowCursor)
        hlayout.addWidget(self.__browse_button)

    def setFileMode(self, mode: QFileDialog.FileMode) -> None:
        """
        Sets the file mode of the file dialog.

        Args:
            mode (QFileDialog.FileMode): File mode.
        """

        self.__file_mode = mode

    def setNameFilters(self, filters: list[str]) -> None:
        """
        Sets the name filters of the file dialog.

        Args:
            filters (list[str]): Name filters.
        """

        self.__filters = filters

    def getPath(self, absolute: bool = False) -> Path:
        """
        Returns the current path.

        Args:
            absolute (bool, optional):
                Whether to join the path with the base path, if any. Defaults to False.

        Returns:
            Path: Current path
        """

        if absolute and self.__base_path is not None:
            return self.__base_path.joinpath(self.text())

        return Path(self.text())

    def setPath(self, path: Path) -> None:
        """
        Sets the current path.

        Args:
            path (Path): New path.
        """

        current_text: str = self.text().strip()

        if self.__base_path is not None and path.is_relative_to(self.__base_path):
            self.setText(str(path.relative_to(self.__base_path)))
        else:
            self.setText(str(path))

        self.pathChanged.emit(Path(current_text), path)

    def isEmpty(self) -> bool:
        """
        Returns:
            bool: If the line edit is empty.
        """

        return self.text().strip() == ""

    def __browse(self) -> None:
        current_text: str = self.text().strip()

        file_dialog = QFileDialog()
        file_dialog.setFileMode(self.__file_mode)
        if self.__filters is not None:
            file_dialog.setNameFilters(self.__filters)

        if current_text:
            current_path: Path = self.getPath(absolute=True)
            file_dialog.setDirectory(str(current_path.parent))
            file_dialog.selectFile(current_path.name)

        if file_dialog.exec():
            selected_files: list[str] = file_dialog.selectedFiles()

            if selected_files:
                file: Path = Path(selected_files.pop())

                self.setPath(file)


def test() -> None:
    from PySide6.QtWidgets import QApplication

    app = QApplication()

    edit = BrowseLineEdit()
    edit.setFileMode(QFileDialog.FileMode.AnyFile)
    edit.show()

    app.exec()


if __name__ == "__main__":
    test()
