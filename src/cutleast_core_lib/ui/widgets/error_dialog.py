"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from ..utilities.icon_provider import IconProvider
from .copy_button import CopyButton


class ErrorDialog(QDialog):
    """
    Custom error dialog.
    """

    MAX_INITIAL_LABEL_WIDTH: int = 800
    """The maximum width the label may have initially."""

    __text: str
    __details: str
    __yesno: bool

    __vlayout: QVBoxLayout

    __details_box: QPlainTextEdit
    __toggle_details_button: QPushButton

    def __init__(
        self,
        parent: Optional[QWidget],
        title: str,
        text: str,
        details: str,
        yesno: bool = True,
    ) -> None:
        """
        Args:
            parent (Optional[QWidget]): Parent widget.
            title (str): Title of the dialog.
            text (str): Short error text.
            details (str): Detailed error text.
            yesno (bool, optional):
                Whether to show yes/no buttons or an ok button. Defaults to True.
        """

        super().__init__(parent)

        self.__text = text
        self.__details = details
        self.__yesno = yesno

        self.setWindowTitle(title)

        self.__init_ui()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        hlayout = QHBoxLayout()
        hlayout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.__vlayout.addLayout(hlayout)

        icon_label = QLabel()
        icon_label.setPixmap(
            self.style()
            .standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)
            .pixmap(32, 32)
        )
        hlayout.addWidget(icon_label)

        text_label = QLabel(self.__text)
        hlayout.addWidget(text_label, stretch=1)
        # calculate the required width of the label without word wrap
        # and set it as the initial minimum width (limited by MAX_INITIAL_LABEL_WIDTH)
        text_label.adjustSize()
        width_hint: int = min(
            ErrorDialog.MAX_INITIAL_LABEL_WIDTH, text_label.sizeHint().width()
        )
        text_label.setWordWrap(True)
        text_label.setMinimumWidth(width_hint)

        self.__details_box = QPlainTextEdit(self.__details)
        self.__details_box.setObjectName("monospace")
        self.__details_box.setMinimumHeight(50)
        self.__details_box.setReadOnly(True)
        self.__vlayout.addWidget(self.__details_box, stretch=1)
        self.__details_box.hide()

        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        hlayout.addStretch()

        if self.__yesno:
            yes_button = QPushButton(self.tr("Continue"))
            yes_button.setDefault(True)
            yes_button.clicked.connect(self.reject)
            hlayout.addWidget(yes_button)

            no_button = QPushButton(self.tr("Exit"))
            no_button.clicked.connect(self.accept)
            hlayout.addWidget(no_button)
        else:
            ok_button = QPushButton(self.tr("Ok"))
            ok_button.setDefault(True)
            ok_button.clicked.connect(self.reject)
            hlayout.addWidget(ok_button)

        copy_button = CopyButton()
        copy_button.setToolTip(self.tr("Copy error details..."))
        copy_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.__details)
        )
        hlayout.addWidget(copy_button)

        if self.__details:
            self.__toggle_details_button = QPushButton()
            self.__toggle_details_button.setToolTip(self.tr("Show details..."))
            self.__toggle_details_button.setIcon(
                IconProvider.get_qta_icon("fa5s.chevron-down")
            )
            self.__toggle_details_button.clicked.connect(self.__toggle_details)
            hlayout.addWidget(self.__toggle_details_button)

    def __toggle_details(self) -> None:
        if not self.__details_box.isVisible():
            self.__details_box.show()
            self.__toggle_details_button.setIcon(
                IconProvider.get_qta_icon("fa5s.chevron-up")
            )
            self.__toggle_details_button.setToolTip(self.tr("Hide details..."))
        else:
            self.__details_box.hide()
            self.__toggle_details_button.setIcon(
                IconProvider.get_qta_icon("fa5s.chevron-down")
            )
            self.__toggle_details_button.setToolTip(self.tr("Show details..."))

        self.adjustSize()
