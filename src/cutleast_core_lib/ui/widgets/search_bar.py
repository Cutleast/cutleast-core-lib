"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton

from ..utilities.icon_provider import IconProvider


class SearchBar(QLineEdit):
    """
    Adapted QLineEdit with search icon, clear button and case sensitivity toggle.
    """

    __live_mode: bool = True

    searchChanged = Signal(str, bool)
    """
    This signal is emitted when the search text changes
    or when the case sensitivity is toggled or when a return is pressed.

    Args:
        str: The search text
        bool: The case sensitivity
    """

    __cs_toggle: QPushButton
    __clear_button: QPushButton
    __search_hint_label: QLabel

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)

        self.addAction(
            IconProvider.get_qta_icon("fa6s.magnifying-glass"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.setPlaceholderText(self.tr("Search..."))

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 5, 0)
        self.setLayout(hlayout)

        hlayout.addStretch()

        self.__search_hint_label = QLabel()
        self.__search_hint_label.setCursor(Qt.CursorShape.ArrowCursor)
        self.__search_hint_label.setPixmap(
            IconProvider.get_qta_icon("mdi6.alert-outline").pixmap(20, 20)
        )
        self.__search_hint_label.setToolTip(
            self.tr("Live search disabled. Press Enter to search.")
        )
        self.__search_hint_label.hide()
        hlayout.addWidget(self.__search_hint_label)

        self.__cs_toggle = QPushButton()
        self.__cs_toggle.setCursor(Qt.CursorShape.ArrowCursor)
        self.__cs_toggle.setIcon(IconProvider.get_qta_icon("mdi6.format-letter-case"))
        self.__cs_toggle.setCheckable(True)
        self.__cs_toggle.clicked.connect(self.setFocus)
        self.__cs_toggle.clicked.connect(self.__on_search_change)
        self.__cs_toggle.setToolTip(self.tr("Toggle case sensitivity"))
        self.__cs_toggle.hide()
        hlayout.addWidget(self.__cs_toggle)

        self.__clear_button = QPushButton()
        self.__clear_button.setCursor(Qt.CursorShape.ArrowCursor)
        self.__clear_button.setIcon(IconProvider.get_qta_icon("mdi6.close"))
        self.__clear_button.clicked.connect(lambda: self.setText(""))
        self.__clear_button.clicked.connect(self.setFocus)
        self.__clear_button.clicked.connect(self.returnPressed.emit)
        self.__clear_button.hide()
        hlayout.addWidget(self.__clear_button)

        self.textChanged.connect(self.__on_text_change)
        self.returnPressed.connect(lambda: self.__on_search_change(True))

        self.setMinimumWidth(180)

    def __on_text_change(self, text: str) -> None:
        self.__clear_button.setVisible(bool(text.strip()))
        self.__cs_toggle.setVisible(bool(text.strip()))

        self.__on_search_change()

    def __on_search_change(self, return_pressed: bool = False) -> None:
        if self.__live_mode or return_pressed:
            self.searchChanged.emit(self.text(), self.__cs_toggle.isChecked())

    def setLiveMode(self, live_mode: bool) -> None:
        """
        Set the live mode state. If live mode is enabled, the search bar
        will emit the `searchChanged` signal when the text changes.
        Otherwise it gets only emitted when a return is pressed.

        Args:
            live_mode (bool): `True` if live mode is enabled, `False` otherwise.
        """

        self.__live_mode = live_mode
        self.__search_hint_label.setVisible(not live_mode)

    def getCaseSensitivity(self) -> bool:
        """
        Get the case sensitivity state.

        Returns:
            bool: `True` if case sensitivity is enabled, `False` otherwise
        """

        return self.__cs_toggle.isChecked()
