"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.ui.widgets.flow_layout import FlowLayout
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtWidgets import QPushButton, QWidget
from pytestqt.qtbot import QtBot


class TestFlowLayout:
    """
    Tests `ui.widgets.flow_layout.FlowLayout`.
    """

    def test_add_take_and_access_items(self, qtbot: QtBot) -> None:
        """
        Tests adding, accessing, and removing layout items.

        Args:
            qtbot (QtBot): Fixture for managing Qt widgets.
        """

        # given
        parent = QWidget()
        layout = FlowLayout(parent)
        button = QPushButton("Button")
        qtbot.addWidget(parent)

        # when
        layout.addWidget(button)
        item = layout.itemAt(0)
        removed_item = layout.takeAt(0)

        # then
        assert item is not None
        assert item.widget() is button
        assert removed_item is item
        assert layout.count() == 0
        assert layout.itemAt(-1) is None
        assert layout.takeAt(1) is None

    def test_wraps_items_to_next_row(self, qtbot: QtBot) -> None:
        """
        Tests that items wrap when the available width is exhausted.

        Args:
            qtbot (QtBot): Fixture for managing Qt widgets.
        """

        # given
        parent = QWidget()
        layout = FlowLayout(parent, margin=5, horizontal_spacing=3, vertical_spacing=7)
        buttons = [QPushButton(str(index)) for index in range(3)]
        qtbot.addWidget(parent)
        for button in buttons:
            button.setFixedSize(QSize(40, 20))
            layout.addWidget(button)

        # when
        layout.setGeometry(QRect(0, 0, 100, 100))

        # then
        assert buttons[0].geometry() == QRect(5, 5, 40, 20)
        assert buttons[1].geometry() == QRect(48, 5, 40, 20)
        assert buttons[2].geometry() == QRect(5, 32, 40, 20)
        assert layout.heightForWidth(100) == 57

    def test_reports_size_and_layout_behavior(self, qtbot: QtBot) -> None:
        """
        Tests minimum size, spacing, height-for-width, and expansion behavior.

        Args:
            qtbot (QtBot): Fixture for managing Qt widgets.
        """

        # given
        parent = QWidget()
        layout = FlowLayout(parent, margin=4, horizontal_spacing=6, vertical_spacing=8)
        button = QPushButton("Button")
        button.setFixedSize(QSize(50, 30))
        qtbot.addWidget(parent)

        # when
        layout.addWidget(button)

        # then
        assert layout.horizontalSpacing() == 6
        assert layout.verticalSpacing() == 8
        assert layout.hasHeightForWidth()
        assert layout.expandingDirections() == Qt.Orientation(0)
        assert layout.minimumSize() == QSize(58, 38)
        assert layout.sizeHint() == layout.minimumSize()
