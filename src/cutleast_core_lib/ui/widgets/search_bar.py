"""
Copyright (c) Cutleast
"""

from typing import Any, override

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton

from cutleast_core_lib.ui.widgets.icon_button import IconButton

from ..utilities.icon_provider import IconProvider


class SearchBar(QLineEdit):
    """
    Adapted QLineEdit with search icon, clear button and case sensitivity toggle.
    """

    DEBOUNCE_INTERVAL_MS: int = 250
    """Delay after text input before emitting the search signal."""

    searchChanged = Signal(str, bool)
    """
    This signal is emitted after debounced text input or an immediate search action.

    Args:
        str: The search text
        bool: The case sensitivity
    """

    __cs_toggle: QPushButton
    __clear_button: QPushButton
    __debounce_timer: QTimer

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        search_icon_action: QAction = self.addAction(
            QIcon(), QLineEdit.ActionPosition.LeadingPosition
        )
        IconProvider.bind_qta_icon(
            search_icon_action, search_icon_action.setIcon, "fa6s.magnifying-glass"
        )

        self.setPlaceholderText(self.tr("Search..."))

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 4, 0)
        self.setLayout(hlayout)

        hlayout.addStretch()

        self.__cs_toggle = IconButton()
        IconProvider.bind_qta_icon(
            self.__cs_toggle, self.__cs_toggle.setIcon, "mdi6.format-letter-case"
        )
        self.__cs_toggle.setCursor(Qt.CursorShape.ArrowCursor)
        self.__cs_toggle.setCheckable(True)
        self.__cs_toggle.clicked.connect(self.setFocus)
        self.__cs_toggle.clicked.connect(self.__emit_search_changed)
        self.__cs_toggle.setToolTip(self.tr("Toggle case sensitivity"))
        self.__cs_toggle.hide()
        hlayout.addWidget(self.__cs_toggle)

        self.__clear_button = IconButton()
        IconProvider.bind_qta_icon(
            self.__clear_button, self.__clear_button.setIcon, "mdi6.close"
        )
        self.__clear_button.setCursor(Qt.CursorShape.ArrowCursor)
        self.__clear_button.clicked.connect(self.__clear_search)
        self.__clear_button.hide()
        hlayout.addWidget(self.__clear_button)

        self.__debounce_timer = QTimer(self)
        self.__debounce_timer.setSingleShot(True)
        self.__debounce_timer.setInterval(self.DEBOUNCE_INTERVAL_MS)
        self.__debounce_timer.timeout.connect(self.__emit_search_changed)

        self.textChanged.connect(self.__on_text_change)
        self.returnPressed.connect(self.__emit_search_changed)

        self.setMinimumWidth(180)

    def __on_text_change(self, text: str) -> None:
        self.__clear_button.setVisible(bool(text.strip()))
        self.__cs_toggle.setVisible(bool(text.strip()))

        self.__debounce_timer.start()

    def __clear_search(self) -> None:
        self.setText("")
        self.setFocus()

        self.__emit_search_changed()

    def __emit_search_changed(self) -> None:
        self.__debounce_timer.stop()
        self.searchChanged.emit(self.text(), self.__cs_toggle.isChecked())

    def getCaseSensitivity(self) -> bool:
        """
        Get the case sensitivity state.

        Returns:
            bool: `True` if case sensitivity is enabled, `False` otherwise
        """

        return self.__cs_toggle.isChecked()
