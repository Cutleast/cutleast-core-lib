"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional

from pyfakefs.fake_filesystem import FakeFilesystem
from PySide6.QtWidgets import QFileDialog, QPushButton
from pytestqt.qtbot import QtBot

from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.browse_edit import BrowseLineEdit


class TestBrowseLineEdit(BaseTest):
    """
    Tests `ui.widgets.browse_edit.BrowseLineEdit`.
    """

    BROWSE_BUTTON: tuple[str, type[QPushButton]] = "browse_button", QPushButton
    """Identifier for accessing the private browse_button field."""

    FILE_MODE: tuple[str, type[QFileDialog.FileMode]] = (
        "file_mode",
        QFileDialog.FileMode,
    )
    """Identifier for accessing the private file_mode field."""

    FILTERS: tuple[str, type[list[str]]] = "filters", list[str]
    """Identifier for accessing the private filters field."""

    def test_initial_state(self, qtbot: QtBot) -> None:
        """
        Tests the initial state of the widget.
        """

        # given
        widget = BrowseLineEdit()
        browse_button: QPushButton = Utils.get_private_field(
            widget, *TestBrowseLineEdit.BROWSE_BUTTON
        )
        file_mode: QFileDialog.FileMode = Utils.get_private_field(
            widget, *TestBrowseLineEdit.FILE_MODE
        )
        filters: Optional[list[str]] = Utils.get_private_field_optional(
            widget, *TestBrowseLineEdit.FILTERS
        )
        qtbot.addWidget(widget)

        # when
        widget.show()

        # then
        assert widget.text() == ""
        assert widget.getPath() == Path()
        assert browse_button.isVisible()
        assert browse_button.isEnabled()
        assert file_mode == QFileDialog.FileMode.AnyFile
        assert filters is None

    def test_set_path_with_base_path(
        self, test_fs: FakeFilesystem, qtbot: QtBot
    ) -> None:
        """
        Tests the `setPath()` method with a set base path.
        """

        # given
        base_path = Path("test")
        base_path.mkdir()
        widget = BrowseLineEdit(base_path=base_path)
        qtbot.addWidget(widget)

        # when
        widget.show()
        widget.setPath(Path("test/file.txt"))

        # then
        assert widget.text() == "file.txt"
        assert widget.getPath() == Path("file.txt")
        assert widget.getPath(absolute=True) == Path("test/file.txt")

    def test_set_path_without_base_path(
        self, test_fs: FakeFilesystem, qtbot: QtBot
    ) -> None:
        """
        Tests the `setPath()` method without a set base path.
        """

        # given
        widget = BrowseLineEdit()
        qtbot.addWidget(widget)

        # when
        widget.show()
        widget.setPath(Path("test/file.txt"))

        # then
        assert widget.text() == "test\\file.txt"
        assert widget.getPath() == Path("test/file.txt")
        assert widget.getPath(absolute=True) == Path("test/file.txt")
