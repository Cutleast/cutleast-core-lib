"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import (
    QApplication,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cutleast_core_lib.core.utilities.typing_utils import checked_cast


class StylesheetEditorWidget(QWidget):
    """
    A widget for live-editing the application stylesheet.
    """

    __vlayout: QVBoxLayout
    __text_edit: QPlainTextEdit
    __apply_button: QPushButton

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

        self.__text_edit.setPlainText(
            checked_cast(QApplication, QApplication.instance()).styleSheet()
        )

        self.__apply_button.clicked.connect(self.__apply_stylesheet)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__text_edit = QPlainTextEdit()
        self.__text_edit.setProperty("monospace", True)
        self.__vlayout.addWidget(self.__text_edit)

        self.__apply_button = QPushButton(self.tr("Apply stylesheet"))
        self.__apply_button.setDefault(True)
        self.__vlayout.addWidget(self.__apply_button)

    def __apply_stylesheet(self) -> None:
        stylesheet: str = self.__text_edit.toPlainText()
        checked_cast(QApplication, QApplication.instance()).setStyleSheet(stylesheet)
