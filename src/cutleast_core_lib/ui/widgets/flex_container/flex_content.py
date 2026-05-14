"""
Copyright (c) Cutleast
"""

from PySide6.QtWidgets import QWidget


class FlexContent(QWidget):
    """
    Base class for any widget that can be used as a child inside a `FlexContainer`.

    Both methods are used by the container to identify panels (for serialization) and to
    display their title in the tile header.
    """

    def get_identifier(self) -> str:
        """
        Returns a persistent, unique string identifier for this panel type.

        The identifier is stored in the serialized layout and used to reconstruct the
        widget tree on the next application start.

        Returns:
            str: A stable identifier that uniquely names this panel type.
        """

        ...

    def get_title(self) -> str:
        """
        Returns the human-readable title of this panel. The title is displayed in the
        tile header alongside the drag handle.

        Returns:
            str: The display title of the panel.
        """

        ...
