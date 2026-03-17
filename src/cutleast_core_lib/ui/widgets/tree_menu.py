"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QCursor

from cutleast_core_lib.ui.utilities.icon_provider import IconProvider

from .menu import Menu


class TreeMenu(Menu):
    """
    Context menu for tree widgets providing expand and collapse actions.
    """

    expand_all_clicked = Signal()
    """Signal emitted when the user clicks on the expand all action."""

    collapse_all_clicked = Signal()
    """Signal emitted when the user clicks on the collapse all action."""

    _expand_all_action: QAction
    _collapse_all_action: QAction

    def __init__(self) -> None:
        super().__init__()

        self.__init_item_actions()

    def __init_item_actions(self) -> None:
        self._expand_all_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.arrow-expand-vertical"),
            self.tr("Expand all"),
        )
        self._expand_all_action.triggered.connect(self.expand_all_clicked.emit)

        self._collapse_all_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.arrow-collapse-vertical"),
            self.tr("Collapse all"),
        )
        self._collapse_all_action.triggered.connect(self.collapse_all_clicked.emit)

        self.addSeparator()

    def open(self, expandable: bool = True) -> None:
        """
        Opens the context menu at the current mouse cursor position.

        Args:
            expandable (bool, optional):
                Toggles the visibility of the expand and collapse actions. Defaults to
                True.
        """

        self._expand_all_action.setVisible(expandable)
        self._collapse_all_action.setVisible(expandable)

        self.exec(QCursor.pos())
