"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import QObject, Signal

from ..utilities.singleton import Singleton
from .alert import Alert


class AlertManager(QObject, Singleton):
    """
    Singleton for managing app-wide alerts (errors, warnings, etc.).
    """

    alert_added = Signal(Alert)
    """
    Signal emitted when a new alert was added.
    
    Args:
        Alert: The added alert.
    """

    alert_removed = Signal(Alert)
    """
    Signal emitted when an alert was removed.
    
    Args:
        Alert: The removed alert.
    """

    __alerts: list[Alert]

    def __init__(self) -> None:  # noqa: D107
        super().__init__()
        Singleton.__init__(self)

        self.__alerts = []

    @property
    def alerts(self) -> list[Alert]:
        """A list of the current app-wide alerts."""

        return self.__alerts.copy()

    def add_alert(self, alert: Alert) -> None:
        """
        Adds an alert to this manager. Does nothing if the alert was already added.

        Args:
            alert (Alert): The alert to add.
        """

        if alert in self.__alerts:
            return

        self.__alerts.append(alert)
        self.alert_added.emit(alert)

    def remove_alert(self, alert: Alert) -> None:
        """
        Removes an alert from this manager. Does nothing, if the alert was not added.

        Args:
            alert (Alert): The alert to remove.
        """

        if alert not in self.__alerts:
            return

        self.__alerts.remove(alert)
        self.alert_removed.emit(alert)
