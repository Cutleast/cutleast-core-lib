"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import ClassVar, Optional, Protocol, cast, override

from pydantic import BaseModel, ConfigDict
from PySide6.QtCore import QByteArray, QEvent, QObject, Signal
from PySide6.QtWidgets import QCheckBox, QWidget

from cutleast_core_lib.core.utilities.singleton import SingletonQObject


class WidgetStateManager(SingletonQObject):
    """
    Class for managing the persistent states of widgets in an application.
    """

    save_requested = Signal()
    """Signal emitted when all widgets are requested to save their states."""

    STATE_PREFIX = "state-"
    GEOMETRY_PREFIX = "geometry-"
    CUSTOM_PREFIX = "custom-"

    class _StateRegistration(QObject):
        """
        QObject-bound registration that saves the state of its parent widget.
        """

        __manager: WidgetStateManager
        __widget_id: str
        __state_getter: Callable[[], QByteArray]

        def __init__(
            self,
            manager: WidgetStateManager,
            widget_id: str,
            state_getter: Callable[[], QByteArray],
            parent: QObject,
        ) -> None:
            """
            Args:
                manager (WidgetStateManager): Manager that persists the state.
                widget_id (str): Unique identifier for the widget state.
                state_getter (Callable[[], QByteArray]): Callback returning the state.
                parent (QObject): Registered widget owning this registration.
            """

            super().__init__(parent)

            self.__manager = manager
            self.__widget_id = widget_id
            self.__state_getter = state_getter

            parent.installEventFilter(self)
            manager.save_requested.connect(self.save_state)

        @override
        def eventFilter(self, watched: QObject, event: QEvent) -> bool:
            """
            Saves the state whenever the registered widget is hidden.

            Hide events are used instead of close events because `QDialog.done()`
            swallows the close event with an internal event filter. Hide events are also
            propagated to all visible descendants of a hidden window.

            Args:
                watched (QObject): Object receiving the event.
                event (QEvent): Event sent to the registered object.

            Returns:
                bool: Whether the event was handled.
            """

            if event.type() == QEvent.Type.Hide:
                self.save_state()

            return super().eventFilter(watched, event)

        def save_state(self) -> None:
            """
            Saves the current state of the registered widget.
            """

            self.__manager.set_state(self.__widget_id, self.__state_getter())

    class _States(BaseModel):
        model_config = ConfigDict(
            ser_json_bytes="base64",
            val_json_bytes="base64",
        )

        states: dict[str, bytes] = {}

    class _HasStateWidget(Protocol):
        destroyed: ClassVar[Signal]

        def restoreState(
            self, state: QByteArray | bytes | bytearray | memoryview, /
        ) -> bool: ...
        def saveState(self, /) -> QByteArray: ...

    __data_path: Path
    __states: _States

    def __init__(self, data_path: Path) -> None:
        """
        Args:
            data_path (Path): Path to the folder where widget states will be stored.
        """

        super().__init__()

        self.__data_path = data_path / "ui_states.json"

        if self.__data_path.is_file():
            self.__states = WidgetStateManager._States.model_validate_json(
                self.__data_path.read_bytes()
            )
        else:
            self.__states = WidgetStateManager._States()

    def register_geometry(self, widget_id: str, widget: QWidget) -> None:
        """
        Registers a widget for geometry state management. This also restores its geometry
        if a saved state is available.

        Args:
            widget_id (str): The unique identifier for the widget.
            widget (QWidget): The widget to be registered.
        """

        state_id: str = WidgetStateManager.GEOMETRY_PREFIX + widget_id

        # Restore the saved geometry state if available
        state: Optional[QByteArray] = self.get_state(state_id)
        if state is not None:
            widget.restoreGeometry(state)

        WidgetStateManager._StateRegistration(
            self, state_id, widget.saveGeometry, widget
        )

    def register_state(self, widget_id: str, widget: _HasStateWidget) -> None:
        """
        Registers a widget for state management. This also restores its state if a saved
        state is available.

        Args:
            widget_id (str): The unique identifier for the widget.
            widget (_HasStateWidget): The widget to be registered.
        """

        state_id: str = WidgetStateManager.STATE_PREFIX + widget_id

        # Restore the saved state if available
        state: Optional[QByteArray] = self.get_state(state_id)
        if state is not None:
            widget.restoreState(state)

        WidgetStateManager._StateRegistration(
            self, state_id, widget.saveState, cast(QObject, widget)
        )

    def register_checkbox(self, widget_id: str, widget: QCheckBox) -> None:
        """
        Registers the check state of a checkbox for state management.

        Args:
            widget_id (str): The unique identifier for the widget.
            widget (QCheckBox): The checkbox to be registered.
        """

        self.register_custom(
            widget_id,
            lambda: QByteArray(bytes(widget.isChecked())),
            lambda state: widget.setChecked(bool(state)),
            widget,
        )

    def register_custom(
        self,
        widget_id: str,
        state_getter: Callable[[], QByteArray],
        state_setter: Callable[[QByteArray], None],
        widget: QWidget,
    ) -> None:
        """
        Registers a custom widget state for management.

        Args:
            widget_id (str): The unique identifier for the widget.
            state_getter (Callable[[], QByteArray]):
                A callable that returns the state as a byte array.
            state_setter (Callable[[QByteArray], None]):
                A callable that applies a byte array to the state.
            widget (QWidget): The widget to be registered.
        """

        state_id: str = WidgetStateManager.STATE_PREFIX + widget_id

        # Restore the saved state if available
        state: Optional[QByteArray] = self.get_state(state_id)
        if state is not None:
            state_setter(state)

        WidgetStateManager._StateRegistration(self, state_id, state_getter, widget)

    def get_state(self, widget_id: str) -> Optional[QByteArray]:
        """
        Gets the state for a specified widget ID.

        Args:
            widget_id (str): The widget identifier.

        Returns:
            Optional[QByteArray]: QByteArray or None.
        """

        state_bytes: Optional[bytes] = self.__states.states.get(widget_id)
        if state_bytes is not None:
            return QByteArray(state_bytes)

    def set_state(self, widget_id: str, state: QByteArray) -> None:
        """
        Sets the state for a specified widget ID.

        Args:
            widget_id (str): The widget identifier.
            state (QByteArray): The state to be saved.
        """

        self.__states.states[widget_id] = bytes(state.data())

    def clear(self) -> None:
        """
        Clears all saved widget states.
        """

        self.__states.states.clear()
        self.__data_path.unlink(missing_ok=True)

    def save(self) -> None:
        """
        Requests all widgets to save their states and then saves the states to a JSON
        file.
        """

        self.save_requested.emit()

        self.__data_path.write_text(self.__states.model_dump_json())
