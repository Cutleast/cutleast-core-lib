"""
Copyright (c) Cutleast
"""

import webbrowser
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from ..utilities.icon_provider import IconProvider
from .tab_widget import TabWidget


class AboutDialog(QDialog):
    """
    About dialog.
    """

    def __init__(
        self,
        app_name: str,
        app_version: str,
        app_icon: QIcon,
        app_license: str,
        licenses: dict[str, str],
        text: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            app_name (str): Application name.
            app_version (str): Application version.
            app_icon (QIcon): Application icon.
            app_license (str): Name of the app's license.
            licenses (dict[str, str]):
                Dictionary of used libraries and URL to their license.
            text (Optional[str], optional): Custom text. Defaults to None.
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.setWindowTitle(self.tr("About"))

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        tab_widget = TabWidget()
        tab_widget.setTabBarAlignment(Qt.AlignmentFlag.AlignHCenter)
        vlayout.addWidget(tab_widget)

        about_tab = QWidget()
        tab_widget.addTab(about_tab, self.tr("About"))
        IconProvider.bind_qta_icon(
            tab_widget, lambda icon: tab_widget.setTabIcon(0, icon), "mdi6.information"
        )

        hlayout = QHBoxLayout()
        about_tab.setLayout(hlayout)

        hlayout.addSpacing(25)

        icon_label = QLabel()
        icon_label.setPixmap(app_icon.pixmap(128, 128))
        hlayout.addWidget(icon_label)

        hlayout.addSpacing(15)

        vlayout = QVBoxLayout()
        hlayout.addLayout(vlayout, 1)

        hlayout.addSpacing(25)
        vlayout.addSpacing(25)

        title_label = QLabel(f"{app_name} v{app_version}")
        title_label.setProperty("title", True)
        vlayout.addWidget(title_label)

        if text is None:
            text = self.tr(
                "Created by Cutleast (<a href='https://www.nexusmods.com/users/65733731'>"
                "NexusMods</a> | <a href='https://github.com/cutleast'>GitHub</a> "
                "| <a href='https://ko-fi.com/cutleast'>Ko-Fi</a>)<br><br>Licensed under "
            )
            text += app_license

            # Add translator credit if available
            translator_info: str = self.tr("<<Put your translator information here.>>")
            if translator_info != "<<Put your translator information here.>>":
                text += translator_info

        credits_label = QLabel(text)
        credits_label.setTextFormat(Qt.TextFormat.RichText)
        credits_label.setOpenExternalLinks(True)
        vlayout.addWidget(credits_label)

        vlayout.addSpacing(25)

        licenses_tab = QListWidget()
        tab_widget.addTab(licenses_tab, self.tr("Used Software"))
        IconProvider.bind_qta_icon(
            tab_widget,
            lambda icon: tab_widget.setTabIcon(1, icon),
            "mdi6.script-text-outline",
        )

        licenses_tab.addItems(list(licenses.keys()))

        licenses_tab.itemDoubleClicked.connect(
            lambda item: webbrowser.open(licenses[item.text()])
        )
