"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtWidgets import QPushButton

from cutleast_core_lib.core.alerts.alert import Alert
from cutleast_core_lib.core.alerts.manager import AlertManager
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.icon_provider import IconProvider


class AlertButton(QPushButton):
    """
    An icon button that updates itself when alerts are added or removed.
    """

    @override
    def __init__(self) -> None:
        super().__init__()

        AlertManager.get().alert_added.connect(lambda _: self.__update_icon())
        AlertManager.get().alert_removed.connect(lambda _: self.__update_icon())
        ThemeManager.get().theme_changed.connect(lambda _: self.__update_icon())

        self.__update_icon()

    def __update_icon(self) -> None:
        highest_severity: Optional[Alert.Severity] = max(
            [alert.severity for alert in AlertManager.get().alerts],
            key=lambda severity: severity.value,
            default=None,
        )
        num_alerts: int = len(AlertManager.get().alerts)

        self.setVisible(highest_severity is not None)
        self.setToolTip(
            self.tr("There is currently one alert.")
            if num_alerts == 1
            else self.tr("There are currently {num} alerts.").format(num=num_alerts)
        )
        self.setText(
            self.tr("1 alert")
            if num_alerts == 1
            else self.tr("{num} alerts").format(num=num_alerts)
        )

        if highest_severity is not None:
            self.setStyleSheet(
                "QPushButton { color: " + highest_severity.get_fg_color().name() + "; }"
            )
            IconProvider.bind_custom_icon(self, self.setIcon, highest_severity.get_icon)
