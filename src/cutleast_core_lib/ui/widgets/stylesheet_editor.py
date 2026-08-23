"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cutleast_core_lib.core.utilities.typing_utils import checked_cast

from ..theme.manager import ThemeManager
from ..theme.ui_mode import UiMode
from ..utilities.icon_provider import IconProvider
from ..utilities.widget_inspector import WidgetInspector
from .copy_button import CopyButton
from .enum_dropdown import EnumDropdown
from .icon_button import IconButton
from .search_bar import SearchBar
from .stylesheet_text_edit import StylesheetTextEdit


class StylesheetEditorWidget(QWidget):
    """
    Runtime-only editor for live-testing the application style sheet.
    """

    __inspector: WidgetInspector

    __vlayout: QVBoxLayout

    __search_widget: QWidget
    __search_bar: SearchBar

    __previous_button: QPushButton
    __next_button: QPushButton
    __close_search_button: QPushButton

    __text_edit: StylesheetTextEdit
    __cursor_position_label: QLabel

    __inspection_widget: QWidget
    __widget_info_edit: QLineEdit
    __object_path_edit: QLineEdit
    __copy_path_button: CopyButton
    __selector_edit: QLineEdit
    __copy_selector_button: CopyButton
    __insert_selector_button: QPushButton

    __inspect_button: QPushButton
    __ui_mode_dropdown: EnumDropdown[UiMode]
    __revert_button: QPushButton
    __apply_button: QPushButton

    __find_shortcut: QShortcut
    __escape_shortcut: QShortcut

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__inspector = WidgetInspector(self)

        self.__init_ui()

        self.__text_edit.setPlainText(ThemeManager.get().stylesheet)

        self.__apply_button.clicked.connect(self.__apply_stylesheet)
        self.__revert_button.clicked.connect(self.__revert_stylesheet)
        self.__inspect_button.clicked.connect(self.__toggle_inspector)
        self.__previous_button.clicked.connect(lambda: self.__find(backwards=True))
        self.__next_button.clicked.connect(self.__find)
        self.__close_search_button.clicked.connect(self.__search_widget.hide)
        self.__copy_path_button.copyClicked.connect(self.__copy_object_path)
        self.__copy_selector_button.copyClicked.connect(self.__copy_selector)
        self.__insert_selector_button.clicked.connect(self.__insert_selector)
        self.__search_bar.searchChanged.connect(self.__find_from_search_bar)
        self.__text_edit.searchRequested.connect(self.__show_search)
        self.__text_edit.cursorPositionInfoChanged.connect(self.__update_cursor_position)
        self.__inspector.inspected.connect(self.__on_widget_inspected)
        self.__inspector.cancelled.connect(self.__cancel_inspection)
        self.__find_shortcut.activated.connect(self.__show_search)
        self.__escape_shortcut.activated.connect(self.__handle_escape)
        self.__ui_mode_dropdown.currentValueChanged.connect(self.__on_ui_mode_changed)

        ThemeManager.get().theme_changed.connect(lambda _: self.__on_theme_changed())

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_search_ui()

        self.__text_edit = StylesheetTextEdit()
        self.__vlayout.addWidget(self.__text_edit)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.__vlayout.addLayout(hlayout)

        warning_label = QLabel()
        IconProvider.bind_qta_icon(
            warning_label,
            lambda icon: warning_label.setPixmap(
                icon.pixmap(
                    ThemeManager.get().theme.metrics.icon,
                    ThemeManager.get().theme.metrics.icon,
                ),
            ),
            "mdi6.alert-outline",
            color=IconProvider.Color.Secondary,
        )
        hlayout.addWidget(warning_label)

        runtime_notice = QLabel(
            self.tr(
                "Runtime preview only. Changes are discarded when the application exits."
            )
        )
        runtime_notice.setProperty("secondary", True)
        hlayout.addWidget(runtime_notice)

        hlayout.addStretch()

        self.__cursor_position_label = QLabel(
            self.tr("Line {line}, Column {column}").format(line=1, column=1)
        )
        hlayout.addWidget(self.__cursor_position_label)

        self.__init_inspection_ui()
        self.__init_action_ui()

        self.__find_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        self.__escape_shortcut = QShortcut(QKeySequence("Escape"), self)

    def __init_search_ui(self) -> None:
        self.__search_widget = QWidget()
        search_hlayout = QHBoxLayout(self.__search_widget)
        search_hlayout.setContentsMargins(0, 0, 0, 0)

        self.__search_bar = SearchBar()
        search_hlayout.addWidget(self.__search_bar)

        self.__previous_button = IconButton()
        IconProvider.bind_qta_icon(
            self.__previous_button, self.__previous_button.setIcon, "mdi6.chevron-up"
        )
        self.__previous_button.setToolTip(self.tr("Go to previous occurrence"))
        search_hlayout.addWidget(self.__previous_button)

        self.__next_button = IconButton()
        IconProvider.bind_qta_icon(
            self.__next_button, self.__next_button.setIcon, "mdi6.chevron-down"
        )
        self.__next_button.setToolTip(self.tr("Go to next occurrence"))
        search_hlayout.addWidget(self.__next_button)

        self.__close_search_button = IconButton()
        IconProvider.bind_qta_icon(
            self.__close_search_button, self.__close_search_button.setIcon, "mdi6.close"
        )
        self.__close_search_button.setToolTip(self.tr("Hide search bar"))
        search_hlayout.addWidget(self.__close_search_button)

        self.__search_widget.hide()
        self.__vlayout.addWidget(self.__search_widget)

    def __init_inspection_ui(self) -> None:
        self.__inspection_widget = QWidget()
        self.__vlayout.addWidget(self.__inspection_widget)
        inspection_vlayout = QVBoxLayout(self.__inspection_widget)
        inspection_vlayout.setContentsMargins(0, 0, 0, 0)

        widget_hlayout = QHBoxLayout()
        widget_hlayout.addWidget(QLabel(self.tr("Widget:")))
        self.__widget_info_edit = QLineEdit()
        self.__widget_info_edit.setReadOnly(True)
        widget_hlayout.addWidget(self.__widget_info_edit)
        inspection_vlayout.addLayout(widget_hlayout)

        path_hlayout = QHBoxLayout()
        path_hlayout.addWidget(QLabel(self.tr("Object path:")))
        self.__object_path_edit = QLineEdit()
        self.__object_path_edit.setReadOnly(True)
        path_hlayout.addWidget(self.__object_path_edit)
        self.__copy_path_button = CopyButton()
        path_hlayout.addWidget(self.__copy_path_button)
        inspection_vlayout.addLayout(path_hlayout)

        selector_hlayout = QHBoxLayout()
        selector_hlayout.addWidget(QLabel(self.tr("QSS selector:")))
        self.__selector_edit = QLineEdit()
        self.__selector_edit.setReadOnly(True)
        selector_hlayout.addWidget(self.__selector_edit)
        self.__copy_selector_button = CopyButton()
        selector_hlayout.addWidget(self.__copy_selector_button)
        self.__insert_selector_button = IconButton()
        IconProvider.bind_qta_icon(
            self.__insert_selector_button,
            self.__insert_selector_button.setIcon,
            "mdi6.call-merge",
        )
        self.__insert_selector_button.setToolTip(
            self.tr("Insert selector at cursor position")
        )
        selector_hlayout.addWidget(self.__insert_selector_button)
        inspection_vlayout.addLayout(selector_hlayout)

        self.__inspection_widget.hide()

    def __init_action_ui(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__inspect_button = IconButton()
        IconProvider.bind_qta_icon(
            self.__inspect_button, self.__inspect_button.setIcon, "mdi6.target"
        )
        self.__inspect_button.setCheckable(True)
        self.__inspect_button.setToolTip(
            self.tr(
                "Inspect a widget in the application. Escape or right-click cancels."
            )
        )
        hlayout.addWidget(self.__inspect_button)
        hlayout.addStretch()

        ui_mode_label = QLabel(self.tr("UI mode:"))
        hlayout.addWidget(ui_mode_label)

        self.__ui_mode_dropdown = EnumDropdown(UiMode, ThemeManager.get().ui_mode)
        hlayout.addWidget(self.__ui_mode_dropdown)

        self.__revert_button = QPushButton(self.tr("Revert runtime stylesheet"))
        hlayout.addWidget(self.__revert_button)

        self.__apply_button = QPushButton(self.tr("Apply runtime stylesheet"))
        self.__apply_button.setDefault(True)
        hlayout.addWidget(self.__apply_button)

    def __apply_stylesheet(self) -> None:
        checked_cast(QApplication, QApplication.instance()).setStyleSheet(
            self.__text_edit.toPlainText()
        )

    def __revert_stylesheet(self, apply: bool = True) -> None:
        stylesheet: str = ThemeManager.get().stylesheet
        self.__text_edit.setPlainText(stylesheet)

        if apply:
            checked_cast(QApplication, QApplication.instance()).setStyleSheet(stylesheet)

    def __show_search(self) -> None:
        self.__search_widget.show()
        selected = self.__text_edit.textCursor().selectedText()

        if selected and "\u2029" not in selected:
            self.__search_bar.setText(selected)

        self.__search_bar.setFocus()
        self.__search_bar.selectAll()

    def __find(self, backwards: bool = False) -> None:
        self.__text_edit.find_text(
            self.__search_bar.text(),
            backwards=backwards,
            case_sensitive=self.__search_bar.getCaseSensitivity(),
        )

    def __find_from_search_bar(self, _text: str, _case_sensitive: bool) -> None:
        self.__find()

    def __toggle_inspector(self, enabled: bool) -> None:
        """
        Starts or stops the widget inspector.

        Args:
            enabled (bool): Whether inspection should be active.
        """

        if enabled:
            self.__inspector.start()
        else:
            self.__inspector.stop(cancelled=True)

    def __on_widget_inspected(
        self, object_path: str, selector: str, class_name: str, object_name: str
    ) -> None:
        """
        Displays details of an inspected widget.

        Args:
            object_path (str): Object hierarchy path.
            selector (str): Generated QSS selector.
            class_name (str): Inspected widget class name.
            object_name (str): Inspected widget object name.
        """

        self.__inspect_button.setChecked(False)
        self.__widget_info_edit.setText(
            f"{class_name} - {object_name}" if object_name else class_name
        )
        self.__object_path_edit.setText(object_path)
        self.__selector_edit.setText(selector)
        self.__inspection_widget.show()

        QApplication.setActiveWindow(self)

    def __insert_selector(self) -> None:
        selector = self.__selector_edit.text()
        if not selector:
            return

        cursor = self.__text_edit.textCursor()
        if cursor.position() > 0 and not self.__text_edit.toPlainText().endswith("\n"):
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText("\n\n")

        cursor.insertText(f"{selector} {{\n{self.__text_edit.indent_text}\n}}")
        cursor.movePosition(QTextCursor.MoveOperation.Up)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
        self.__text_edit.setTextCursor(cursor)
        self.__text_edit.setFocus()

    def __copy_object_path(self) -> None:
        QApplication.clipboard().setText(self.__object_path_edit.text())

    def __copy_selector(self) -> None:
        QApplication.clipboard().setText(self.__selector_edit.text())

    def __cancel_inspection(self) -> None:
        self.__inspect_button.setChecked(False)

    def __update_cursor_position(self, line: int, column: int) -> None:
        self.__cursor_position_label.setText(
            self.tr("Line {line}, Column {column}").format(line=line, column=column)
        )

    def __handle_escape(self) -> None:
        if self.__inspector.active:
            self.__inspector.stop(cancelled=True)
        elif self.__search_widget.isVisible():
            self.__search_widget.hide()
            self.__text_edit.setFocus()

    def __on_ui_mode_changed(self, new_ui_mode: UiMode) -> None:
        """
        Slot for handling the UI mode change signal from the dropdown.

        Args:
            new_ui_mode (UiMode): The new UI mode.
        """

        ThemeManager.get().set_ui_mode(new_ui_mode)

    def __on_theme_changed(self) -> None:
        """
        Slot for handling the theme change signal from the ThemeManager.
        """

        self.__ui_mode_dropdown.blockSignals(True)
        self.__ui_mode_dropdown.setCurrentValue(ThemeManager.get().ui_mode)
        self.__ui_mode_dropdown.blockSignals(False)

        messagebox = QMessageBox()
        messagebox.setIcon(QMessageBox.Icon.Information)
        messagebox.setWindowTitle(self.tr("Theme changed"))
        messagebox.setText(
            self.tr(
                "The application theme has changed. Do you want to reset the stylesheet "
                "to the current theme?"
            )
        )
        messagebox.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        messagebox.setDefaultButton(QMessageBox.StandardButton.Yes)
        ThemeManager.update_widget_styles(messagebox)

        if messagebox.exec() == QMessageBox.StandardButton.Yes:
            self.__revert_stylesheet(apply=False)

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Stops active widget inspection before closing the editor.

        Args:
            event (QCloseEvent): Close event to process.
        """

        self.__inspector.stop()
        super().closeEvent(event)
