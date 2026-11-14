"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cutleast_core_lib.core.alerts.alert import Alert
from cutleast_core_lib.core.alerts.manager import AlertManager
from cutleast_core_lib.core.utilities.datetime import fmt_timestamp
from cutleast_core_lib.core.utilities.filter import matches_filter
from cutleast_core_lib.core.utilities.typing_utils import checked_cast
from cutleast_core_lib.ui.alerts.toolbar import AlertsToolBar
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.theme.models.theme import Theme
from cutleast_core_lib.ui.utilities.column_config import (
    ColumnConfig,
    ColumnEnum,
    TreeItem,
)
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.utilities.tree_widget import get_visible_top_level_item_count
from cutleast_core_lib.ui.widgets.search_bar import SearchBar

from .details_widget import AlertDetailsWidget


class AlertWidget(QWidget):
    """
    Widget for displaying the current app-wide alerts.
    """

    class Columns(ColumnEnum):
        """The columns of the alert list."""

        Timestamp = ColumnConfig[Alert](
            title_supplier=lambda: QApplication.translate(
                "AlertWidget.Columns", "Timestamp"
            ),
            display_text_getter=lambda alert: fmt_timestamp(alert.timestamp, "%H:%M:%S"),
            sort_key_getter=lambda alert: alert.timestamp,
            tooltip_getter=lambda alert: fmt_timestamp(alert.timestamp),
        )
        Severity = ColumnConfig[Alert](
            title_supplier=lambda: QApplication.translate(
                "AlertWidget.Columns", "Severity"
            ),
            display_text_getter=lambda alert: alert.severity.get_localized_name(),
            sort_key_getter=lambda alert: alert.severity.value,
            tooltip_getter=lambda alert: alert.severity.get_localized_description(),
            icon_getter=lambda alert: alert.severity.get_icon(),
            background_color_getter=lambda alert: alert.severity.get_bg_color(),
            hover_background_color_getter=lambda alert: (
                alert.severity.get_highlighted_bg_color()
            ),
            foreground_color_getter=lambda alert: alert.severity.get_fg_color(),
        )
        Title = ColumnConfig[Alert](
            title_supplier=lambda: QApplication.translate(
                "AlertWidget.Columns", "Title"
            ),
            display_text_getter=lambda alert: alert.title,
        )

    __alert_items: dict[Alert, TreeItem[Alert]]

    __vlayout: QVBoxLayout
    __splitter: QSplitter

    __tool_bar: AlertsToolBar
    __search_bar: SearchBar
    __num_label: QLabel
    __tree_widget: QTreeWidget

    __alert_details_widget: AlertDetailsWidget

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__alert_items = {}

        self.__init_ui()

        self.__tool_bar.filter_changed.connect(lambda *_: self.__update_list())
        self.__search_bar.searchChanged.connect(lambda *_: self.__update_list())
        self.__tree_widget.currentItemChanged.connect(
            lambda cur, prev: self.__on_item_selected(cur)
        )

        self.__alert_details_widget.remove_requested.connect(
            self.__dismiss_current_alert
        )

        ThemeManager.get().theme_changed.connect(self.__on_theme_changed)

        alert_manager: AlertManager = AlertManager.get()
        alert_manager.alert_added.connect(self.__add_alert)
        alert_manager.alert_removed.connect(self.__remove_alert)

        for alert in alert_manager.alerts:
            self.__add_alert(alert)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__splitter = QSplitter(Qt.Orientation.Horizontal)
        self.__vlayout.addWidget(self.__splitter, stretch=1)

        self.__init_alerts_list()
        self.__init_alert_widget()

        self.__splitter.setSizes([100_000, 100_000])
        # WidgetStateManager.get().register_state("alert_widget/splitter", self.__splitter)

    def __init_alerts_list(self) -> None:
        list_widget = QWidget()
        self.__splitter.addWidget(list_widget)

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        list_widget.setLayout(vlayout)

        self.__tool_bar = AlertsToolBar()
        vlayout.addWidget(self.__tool_bar)

        filter_action: QAction = self.__tool_bar.actions()[0]

        title_label = QLabel(self.tr("Current alerts"))
        title_label.setProperty("title", True)
        self.__tool_bar.insertWidget(filter_action, title_label)

        self.__tool_bar.insertSeparator(filter_action)

        self.__search_bar = SearchBar()
        self.__tool_bar.addWidget(self.__search_bar)

        self.__tool_bar.addSeparator()

        self.__num_label = QLabel("0")
        self.__num_label.setToolTip(self.tr("Number of alerts"))
        self.__num_label.setProperty("subtitle", True)
        self.__tool_bar.addWidget(self.__num_label)

        self.__tree_widget = QTreeWidget()
        AlertWidget.Columns.apply_to_tree_widget(self.__tree_widget)
        self.__tree_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.__tree_widget.setSortingEnabled(True)
        self.__tree_widget.sortByColumn(
            AlertWidget.Columns.Timestamp.index, Qt.SortOrder.DescendingOrder
        )
        vlayout.addWidget(self.__tree_widget)

        WidgetStateManager.get().register_state(
            "alert_widget/tree_widget_header", self.__tree_widget.header()
        )

        footer_hlayout = QHBoxLayout()
        footer_hlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.addLayout(footer_hlayout)

        info_icon = QLabel()
        IconProvider.bind_qta_icon(
            info_icon,
            lambda icon: info_icon.setPixmap(
                icon.pixmap(
                    ThemeManager.get().theme.metrics.icon,
                    ThemeManager.get().theme.metrics.icon,
                )
            ),
            "mdi6.information",
            color=IconProvider.Color.Secondary,
        )
        footer_hlayout.addWidget(info_icon)

        info_label = QLabel(
            self.tr(
                "Here you can find all notices, warnings and errors that occured in "
                "batch or background operations."
            )
        )
        info_label.setProperty("secondary", True)
        info_label.setWordWrap(True)
        footer_hlayout.addWidget(info_label, stretch=1)

    def __init_alert_widget(self) -> None:
        self.__alert_details_widget = AlertDetailsWidget()
        self.__splitter.addWidget(self.__alert_details_widget)

    def __on_theme_changed(self, _: Theme) -> None:
        for item in self.__alert_items.values():
            item.update()

    def __on_item_selected(self, item: Optional[QTreeWidgetItem]) -> None:
        if (
            isinstance(item, TreeItem)
            and get_visible_top_level_item_count(self.__tree_widget) > 0
        ):
            self.__alert_details_widget.set_alert(checked_cast(Alert, item.item))
        else:
            self.__alert_details_widget.set_alert(None)

    def __add_alert(self, alert: Alert) -> None:
        alert_item = TreeItem[Alert](alert, AlertWidget.Columns)
        self.__alert_items[alert] = alert_item
        self.__tree_widget.addTopLevelItem(alert_item)
        self.__update_list()

    def __remove_alert(self, alert: Alert) -> None:
        alert_item: Optional[TreeItem[Alert]] = self.__alert_items.pop(alert, None)
        if alert_item is not None:
            self.__tree_widget.takeTopLevelItem(
                self.__tree_widget.indexOfTopLevelItem(alert_item)
            )
            self.__update_list()

    def __dismiss_current_alert(self) -> None:
        current_item: Optional[QTreeWidgetItem] = self.__tree_widget.currentItem()
        if isinstance(current_item, TreeItem) and isinstance(current_item.item, Alert):
            AlertManager.get().remove_alert(current_item.item)

    def __update_list(self) -> None:
        text_filter: Optional[str] = self.__search_bar.text().strip() or None
        case_sensitive: bool = self.__search_bar.getCaseSensitivity()
        checked_severities: list[Alert.Severity] = self.__tool_bar.checked_items

        for alert, item in self.__alert_items.items():
            alert_text: str = (
                alert.title + alert.summary + alert.details + str(alert.context)
            )
            item.setHidden(
                not matches_filter(alert_text, text_filter, case_sensitive)
                or alert.severity not in checked_severities
            )

        self.__num_label.setText(
            str(
                len(
                    [item for item in self.__alert_items.values() if not item.isHidden()]
                )
            )
        )
