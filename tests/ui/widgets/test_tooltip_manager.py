"""
Copyright (c) Cutleast
"""

from collections.abc import Generator
from types import SimpleNamespace
from typing import Any

import pytest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.tooltip_manager import TooltipManager
from cutleast_core_lib.ui.widgets.tooltip_popup import TooltipPopup
from PySide6.QtCore import QEvent, QObject, QPoint, QRect, Signal
from PySide6.QtGui import QHelpEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
)
from pytestqt.qtbot import QtBot


def _hide_immediately_type() -> None:
    """
    Provides a callable type for accessing the manager's private test seam.
    """


class _ThemeManagerStub(QObject):
    """
    Minimal theme-manager replacement used for tooltip widget tests.
    """

    theme_changed = Signal(object)
    """
    Signal emitted when the test theme changes.

    Args:
        object: The updated test theme.
    """

    theme: Any

    def __init__(self, theme: Any) -> None:
        """
        Initializes the test theme manager.

        Args:
            theme (Any): Initial theme supplied to tested widgets.
        """

        super().__init__()

        self.theme = theme


class TestTooltipManager:
    """
    Tests `ui.widgets.tooltip_manager.TooltipManager`.
    """

    POPUP: tuple[str, type[TooltipPopup]] = "popup", TooltipPopup
    """Identifier for accessing the manager's custom tooltip popup."""

    @pytest.fixture
    def tooltip_manager(
        self, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
    ) -> Generator[tuple[TooltipManager, _ThemeManagerStub]]:
        """
        Creates an initialized tooltip manager with a controllable test theme.

        Args:
            monkeypatch (pytest.MonkeyPatch): Fixture for replacing global lookups.
            qtbot (QtBot): Fixture for managing Qt widgets.

        Yields:
            Generator[tuple[TooltipManager, _ThemeManagerStub]]:
                Manager and its test theme manager.
        """

        # given
        theme = SimpleNamespace(
            metrics=SimpleNamespace(shadow_margin=12, shadow_size=8),
            colors=SimpleNamespace(shadow="#96000000"),
            resolve=lambda _: "#96000000",
        )
        theme_manager = _ThemeManagerStub(theme)
        monkeypatch.setattr(
            ThemeManager,
            "get",
            classmethod(lambda _: theme_manager),
        )
        Utils.reset_singleton(TooltipManager)
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        manager = TooltipManager(app)

        # when
        yield manager, theme_manager

        # then
        hide_immediately = Utils.get_private_method(
            manager,
            "hide_immediately",
            _hide_immediately_type,
        )
        hide_immediately()
        app.removeEventFilter(manager)
        Utils.reset_singleton(TooltipManager)

    def test_show_text_displays_and_hides_custom_tooltip(
        self,
        tooltip_manager: tuple[TooltipManager, _ThemeManagerStub],
        qtbot: QtBot,
    ) -> None:
        """
        Tests that the manual tooltip API displays and hides its popup.

        Args:
            tooltip_manager (tuple[TooltipManager, _ThemeManagerStub]): Manager fixture.
            qtbot (QtBot): Fixture for managing Qt widgets.
        """

        # given
        manager, _ = tooltip_manager
        button = QPushButton("Button")
        qtbot.addWidget(button)
        button.move(100, 100)
        button.show()

        # when
        manager.show_text(
            button.mapToGlobal(QPoint(1, 1)),
            "<b>Tooltip</b>",
            button,
            button.rect(),
            1_000,
        )

        # then
        assert manager.is_visible
        assert manager.text == "<b>Tooltip</b>"
        popup = Utils.get_private_field(manager, *TestTooltipManager.POPUP)
        content_frame = popup.findChild(QFrame, "content_frame")
        assert content_frame is not None
        assert content_frame.mapToGlobal(QPoint()) == button.mapToGlobal(QPoint(3, 17))

        # when
        hide_immediately = Utils.get_private_method(
            manager,
            "hide_immediately",
            _hide_immediately_type,
        )
        hide_immediately()

        # then
        qtbot.waitUntil(lambda: not manager.is_visible)
        assert manager.text == ""

    def test_tooltip_event_replaces_widget_tooltip(
        self,
        tooltip_manager: tuple[TooltipManager, _ThemeManagerStub],
        qtbot: QtBot,
    ) -> None:
        """
        Tests that a widget tooltip event is displayed by the custom manager.

        Args:
            tooltip_manager (tuple[TooltipManager, _ThemeManagerStub]): Manager fixture.
            qtbot (QtBot): Fixture for managing Qt widgets.
        """

        # given
        manager, _ = tooltip_manager
        button = QPushButton("Button")
        button.setToolTip("Widget tooltip")
        qtbot.addWidget(button)
        button.show()
        position = QPoint(1, 1)
        event = QHelpEvent(
            QEvent.Type.ToolTip,
            position,
            button.mapToGlobal(position),
        )

        # when
        QApplication.sendEvent(button, event)

        # then
        assert manager.is_visible
        assert manager.text == "Widget tooltip"
        assert event.isAccepted()

    def test_tooltip_hides_after_explicit_display_time(
        self,
        tooltip_manager: tuple[TooltipManager, _ThemeManagerStub],
        qtbot: QtBot,
    ) -> None:
        """
        Tests that an explicit display time expires the custom tooltip.

        Args:
            tooltip_manager (tuple[TooltipManager, _ThemeManagerStub]): Manager fixture.
            qtbot (QtBot): Fixture for managing Qt widgets.
        """

        # given
        manager, _ = tooltip_manager
        button = QPushButton("Button")
        qtbot.addWidget(button)
        button.show()

        # when
        manager.show_text(
            button.mapToGlobal(QPoint(1, 1)),
            "Tooltip",
            button,
            button.rect(),
            1,
        )

        # then
        qtbot.waitUntil(lambda: not manager.is_visible)

    def test_leave_event_hides_tooltip_after_delay(
        self,
        tooltip_manager: tuple[TooltipManager, _ThemeManagerStub],
        qtbot: QtBot,
    ) -> None:
        """
        Tests that leaving a tooltip source hides the popup after the normal delay.

        Args:
            tooltip_manager (tuple[TooltipManager, _ThemeManagerStub]): Manager fixture.
            qtbot (QtBot): Fixture for managing Qt widgets.
        """

        # given
        manager, _ = tooltip_manager
        button = QPushButton("Button")
        qtbot.addWidget(button)
        button.show()
        manager.show_text(
            button.mapToGlobal(QPoint(1, 1)),
            "Tooltip",
            button,
            button.rect(),
        )

        # when
        QApplication.sendEvent(button, QEvent(QEvent.Type.Leave))

        # then
        qtbot.waitUntil(lambda: not manager.is_visible, timeout=1_000)

    def test_tooltip_event_resolves_item_view_tooltip(
        self,
        tooltip_manager: tuple[TooltipManager, _ThemeManagerStub],
        qtbot: QtBot,
    ) -> None:
        """
        Tests that a tooltip event resolves an item view's tooltip role.

        Args:
            tooltip_manager (tuple[TooltipManager, _ThemeManagerStub]): Manager fixture.
            qtbot (QtBot): Fixture for managing Qt widgets.
        """

        # given
        manager, _ = tooltip_manager
        tree_widget = QTreeWidget()
        tree_widget.setColumnCount(1)
        item = QTreeWidgetItem(["Item"])
        item.setToolTip(0, "Item tooltip")
        tree_widget.addTopLevelItem(item)
        qtbot.addWidget(tree_widget)
        tree_widget.show()
        qtbot.waitUntil(lambda: tree_widget.visualItemRect(item).isValid())
        position = tree_widget.visualItemRect(item).center()
        viewport = tree_widget.viewport()
        event = QHelpEvent(
            QEvent.Type.ToolTip,
            position,
            viewport.mapToGlobal(position),
        )

        # when
        QApplication.sendEvent(viewport, event)

        # then
        assert manager.is_visible
        assert manager.text == "Item tooltip"
        assert event.isAccepted()

    def test_theme_change_updates_popup_shadow_metrics(
        self,
        tooltip_manager: tuple[TooltipManager, _ThemeManagerStub],
        qtbot: QtBot,
    ) -> None:
        """
        Tests that a theme change updates the custom popup shadow settings.

        Args:
            tooltip_manager (tuple[TooltipManager, _ThemeManagerStub]): Manager fixture.
            qtbot (QtBot): Fixture for managing Qt widgets.
        """

        # given
        manager, theme_manager = tooltip_manager
        button = QPushButton("Button")
        qtbot.addWidget(button)
        button.show()
        manager.show_text(
            button.mapToGlobal(QPoint(1, 1)),
            "Tooltip",
            button,
            QRect(button.rect()),
        )
        popup = Utils.get_private_field(manager, *TestTooltipManager.POPUP)
        updated_theme = SimpleNamespace(
            metrics=SimpleNamespace(shadow_margin=17, shadow_size=5),
            colors=SimpleNamespace(shadow="#46000000"),
            resolve=lambda _: "#46000000",
        )

        # when
        theme_manager.theme_changed.emit(updated_theme)

        # then
        layout = popup.layout()
        assert layout is not None
        assert layout.contentsMargins().left() == 17
        content_frame = popup.findChild(QFrame, "content_frame")
        assert content_frame is not None
        effect = content_frame.graphicsEffect()
        assert isinstance(effect, QGraphicsDropShadowEffect)
        assert effect.blurRadius() == 5
