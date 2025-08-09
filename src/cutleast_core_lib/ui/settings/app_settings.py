"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.config.app_config import AppConfig
from cutleast_core_lib.core.config.exceptions import ConfigValidationError
from cutleast_core_lib.core.config.validation_utils import ValidationUtils
from cutleast_core_lib.core.utilities.filesystem import get_folder_size
from cutleast_core_lib.core.utilities.logger import Logger
from cutleast_core_lib.core.utilities.scale import scale_value

from ..widgets.color_edit import ColorLineEdit
from ..widgets.enum_dropdown import EnumDropdown
from .settings_page import SettingsPage


class AppSettings(SettingsPage[AppConfig]):
    """
    Page for application settings.
    """

    cache: Optional[Cache]

    __vlayout: QVBoxLayout
    __logs_num_box: QSpinBox
    __log_level_box: EnumDropdown[Logger.Level]
    __accent_color_entry: ColorLineEdit
    __clear_cache_button: QPushButton

    def __init__(self, initial_config: AppConfig) -> None:
        self.cache = Cache.get()

        super().__init__(initial_config)

        self.__clear_cache_button.setVisible(self.cache is not None)

        self.__logs_num_box.valueChanged.connect(lambda _: self.changed_signal.emit())
        self.__logs_num_box.valueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        self.__log_level_box.currentValueChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__log_level_box.currentValueChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )
        self.__accent_color_entry.textChanged.connect(
            lambda _: self.changed_signal.emit()
        )
        self.__accent_color_entry.textChanged.connect(
            lambda _: self.restart_required_signal.emit()
        )

    @override
    def _init_ui(self) -> None:
        scroll_widget = QWidget()
        scroll_widget.setObjectName("transparent")
        self.setWidget(scroll_widget)

        self.__vlayout = QVBoxLayout()
        scroll_widget.setLayout(self.__vlayout)

        self.__init_basic_settings()

    def __init_basic_settings(self) -> None:
        basic_group = QGroupBox(self.tr("Basic App Settings"))
        self.__vlayout.addWidget(basic_group)
        basic_flayout = QFormLayout()
        basic_group.setLayout(basic_flayout)

        self.__logs_num_box = QSpinBox()
        self.__logs_num_box.installEventFilter(self)
        self.__logs_num_box.setRange(-1, 100)
        self.__logs_num_box.setValue(self._initial_config.log_num_of_files)
        basic_flayout.addRow(
            "*" + self.tr("Number of newest log files to keep"), self.__logs_num_box
        )

        self.__log_level_box = EnumDropdown(
            Logger.Level, self._initial_config.log_level
        )
        self.__log_level_box.installEventFilter(self)
        basic_flayout.addRow("*" + self.tr("Log Level"), self.__log_level_box)

        self.__accent_color_entry = ColorLineEdit(
            [AppConfig.get_default_value("accent_color", str)]
        )
        self.__accent_color_entry.installEventFilter(self)
        self.__accent_color_entry.setText(self._initial_config.accent_color)
        basic_flayout.addRow("*" + self.tr("Accent Color"), self.__accent_color_entry)

        self.__clear_cache_button = QPushButton(self.tr("Clear Cache"))
        self.__clear_cache_button.clicked.connect(self.__clear_cache)
        self.__clear_cache_button.setEnabled(
            self.cache is not None and self.cache.path.is_dir()
        )
        if self.cache is not None and self.cache.path.is_dir():
            self.__clear_cache_button.setText(
                self.__clear_cache_button.text()
                + f" ({scale_value(get_folder_size(self.cache.path))})"
            )
        basic_flayout.addRow(self.__clear_cache_button)

    def __clear_cache(self) -> None:
        if self.cache is None:
            return

        self.cache.clear_caches()
        self.__clear_cache_button.setText(self.tr("Clear Cache"))
        self.__clear_cache_button.setEnabled(False)

    @override
    def validate(self) -> None:
        accent_color: str = self.__accent_color_entry.text().strip()

        if not ValidationUtils.is_valid_hex_color(accent_color):
            raise ConfigValidationError(
                self.tr("Accent color must be a valid hexadecimal color code!")
            )

    @override
    def apply(self, config: AppConfig) -> None:
        config.log_num_of_files = self.__logs_num_box.value()
        config.log_level = self.__log_level_box.getCurrentValue()
        config.accent_color = self.__accent_color_entry.text()
