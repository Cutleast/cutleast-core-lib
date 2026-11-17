"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from cutleast_core_lib.core.alerts.alert import Alert
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.utilities.layout import clear_layout
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.widgets.copy_button import CopyButton
from cutleast_core_lib.ui.widgets.elided_label import ElidedLabel
from cutleast_core_lib.ui.widgets.section_area_widget import SectionAreaWidget
from cutleast_core_lib.ui.widgets.smooth_scroll_area import SmoothScrollArea


class AlertDetailsWidget(SmoothScrollArea):
    """
    Widget for displaying details about an alert.
    """

    remove_requested = Signal()
    """Signal emitted when the user wants to remove the current alert."""

    __vlayout: QVBoxLayout

    __alert_icon_label: QLabel
    __alert_title_label: QLabel
    __dismiss_alert_button: QPushButton
    __alert_summary_label: QLabel
    __alert_details_box: QPlainTextEdit
    __alert_copy_details_button: CopyButton
    __alert_context_glayout: QGridLayout

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

        self.__dismiss_alert_button.clicked.connect(self.remove_requested.emit)
        self.__alert_copy_details_button.copyClicked.connect(self.__copy_details)

        self.set_alert(None)

    def __init_ui(self) -> None:
        scroll_widget = QWidget()
        self.setWidget(scroll_widget)
        self.setWidgetResizable(True)

        self.__vlayout = QVBoxLayout()
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_widget.setLayout(self.__vlayout)

        self.__init_header()

        self.__alert_summary_label = QLabel()
        self.__alert_summary_label.setWordWrap(True)
        self.__vlayout.addWidget(self.__alert_summary_label)

        self.__init_details_section()
        self.__init_context_section()

    def __init_header(self) -> None:
        header_hlayout = QHBoxLayout()
        header_hlayout.setContentsMargins(0, 0, 0, 0)
        self.__vlayout.addLayout(header_hlayout)

        self.__alert_icon_label = QLabel()
        header_hlayout.addWidget(self.__alert_icon_label)

        self.__alert_title_label = ElidedLabel()
        self.__alert_title_label.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            self.__alert_title_label.sizePolicy().verticalPolicy(),
        )
        self.__alert_title_label.setMinimumWidth(1)
        self.__alert_title_label.setProperty("subtitle", True)
        header_hlayout.addWidget(self.__alert_title_label)

        header_hlayout.addStretch()

        self.__dismiss_alert_button = QPushButton(self.tr("Dismiss alert"))
        IconProvider.bind_qta_icon(
            self.__dismiss_alert_button,
            self.__dismiss_alert_button.setIcon,
            "mdi6.trash-can",
            color=IconProvider.Color.Destructive,
        )
        self.__dismiss_alert_button.setProperty("transparent", True)
        self.__dismiss_alert_button.setProperty("destructive", True)
        header_hlayout.addWidget(self.__dismiss_alert_button)

    def __init_details_section(self) -> None:
        details_title_label = QLabel(self.tr("Details (e.g. traceback)"))
        details_title_label.setProperty("subtitle", True)

        details_widget = QWidget()
        details_vlayout = QVBoxLayout()
        details_vlayout.setContentsMargins(0, 0, 0, 0)
        details_widget.setLayout(details_vlayout)

        self.__alert_details_box = QPlainTextEdit()
        self.__alert_details_box.setReadOnly(True)
        self.__alert_details_box.setProperty("monospace", True)
        details_vlayout.addWidget(self.__alert_details_box)

        self.__alert_copy_details_button = CopyButton()
        self.__alert_copy_details_button.setText(self.tr("Copy details"))
        details_vlayout.addWidget(
            self.__alert_copy_details_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        details_section = SectionAreaWidget(details_title_label, details_widget)
        self.__vlayout.addWidget(details_section)

        WidgetStateManager.get().register_state(
            "alert_details/details_section", details_section
        )

    def __init_context_section(self) -> None:
        context_title_label = QLabel(self.tr("Additional context"))
        context_title_label.setProperty("subtitle", True)

        context_widget = QWidget()
        self.__alert_context_glayout = QGridLayout()
        self.__alert_context_glayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.__alert_context_glayout.setSpacing(15)
        self.__alert_context_glayout.setColumnStretch(1, 1)
        context_widget.setLayout(self.__alert_context_glayout)

        context_section = SectionAreaWidget(context_title_label, context_widget)
        self.__vlayout.addWidget(context_section)

        WidgetStateManager.get().register_state(
            "alert_details/context_section", context_section
        )

    def __copy_details(self) -> None:
        QApplication.clipboard().setText(self.__alert_details_box.toPlainText())

    def set_alert(self, alert: Optional[Alert]) -> None:
        """
        Sets the alert to be displayed by this widget.

        Args:
            alert (Optional[Alert]):
                The alert to be displayed by this widget or None, if the widget should be
                cleared.
        """

        self.__alert_icon_label.setVisible(alert is not None)
        self.__dismiss_alert_button.setEnabled(alert is not None)
        self.__alert_copy_details_button.setEnabled(alert is not None)
        clear_layout(self.__alert_context_glayout)

        if alert is None:
            self.__alert_title_label.setText("")
            self.__alert_summary_label.setText("")
            self.__alert_details_box.setPlainText("")
            return

        IconProvider.bind_custom_icon(
            self.__alert_icon_label,
            lambda icon: self.__alert_icon_label.setPixmap(
                icon.pixmap(
                    ThemeManager.get().theme.metrics.icon_l,
                    ThemeManager.get().theme.metrics.icon_l,
                )
            ),
            lambda: alert.severity.get_icon(),
        )
        self.__alert_icon_label.setToolTip(alert.severity.get_localized_description())

        self.__alert_title_label.setText(alert.title)
        self.__alert_summary_label.setText(alert.summary)
        self.__alert_details_box.setPlainText(alert.details)

        for p, (property, value) in enumerate(alert.context.items()):
            property_label = QLabel(property)
            self.__alert_context_glayout.addWidget(property_label, p, 0)

            value_label = QLabel(value)
            value_label.setWordWrap(True)
            value_label.setProperty("emphasized", True)
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            value_label.setCursor(Qt.CursorShape.IBeamCursor)
            self.__alert_context_glayout.addWidget(value_label, p, 1)
