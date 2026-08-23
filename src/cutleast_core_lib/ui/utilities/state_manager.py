"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import ClassVar, Optional, Protocol, cast, override

from pydantic import BaseModel, ConfigDict
from PySide6.QtCore import QByteArray, QEvent, QObject, Signal
from PySide6.QtWidgets import QWidget

from cutleast_core_lib.core.utilities.singleton import SingletonQObject


class WidgetStateManager(SingletonQObject):
    """
    Class for managing the persistent states of widgets in an application.
    """

    save_requested = Signal()
    """Signal emitted when all widgets are requested to save their states."""

    STATE_PREFIX = "state-"
    GEOMETRY_PREFIX = "geometry-"

    class _StateRegistration(QObject):
        """
        QObject-bound registration that saves the state of its parent widget.
        """

        __manager: WidgetStateManager
        __widget_id: str
        __state_getter: Callable[[], QByteArray]
        __save_on_hide: bool

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
            self.__save_on_hide = False

        @override
        def eventFilter(self, watched: QObject, event: QEvent) -> bool:
            """
            Saves the state when the registered window was successfully closed.

            Args:
                watched (QObject): Object receiving the event.
                event (QEvent): Event sent to the registered object.

            Returns:
                bool: Whether the event was handled.
            """

            if event.type() == QEvent.Type.Close:
                self.__save_on_hide = True
            elif event.type() == QEvent.Type.Hide and self.__save_on_hide:
                self.save_state()
                self.__save_on_hide = False

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

        registration = WidgetStateManager._StateRegistration(
            self, state_id, widget.saveGeometry, widget
        )
        widget.installEventFilter(registration)
        self.save_requested.connect(registration.save_state)

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

        registration = WidgetStateManager._StateRegistration(
            self, state_id, widget.saveState, cast(QObject, widget)
        )
        self.save_requested.connect(registration.save_state)

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
