"""
Copyright (c) Cutleast
"""

from typing import cast, override

from native_titlebar import NativeWindow
from PySide6.QtCore import QMargins
from PySide6.QtWidgets import QBoxLayout


class ExtendedWindow(NativeWindow):
    """
    Window with a native title bar whose widgets start directly after the window icon
    instead of being offset by the symmetric inset of the native caption buttons.
    """

    TITLE_BAR_LEFT_MARGIN: int = 36
    """
    Left margin of the title bar layout that keeps space for the window icon that is
    painted by the title bar.
    """

    @override
    def _update_titlebar_layout(self) -> None:
        # The title bar resets its margins symmetrically whenever the native metrics
        # change, which is always followed by a call to this method. The base
        # constructor already calls this method, so the layout is looked up lazily.
        title_bar_layout = cast(QBoxLayout, self.titleBar().layout())
        margins: QMargins = title_bar_layout.contentsMargins()
        title_bar_layout.setContentsMargins(
            ExtendedWindow.TITLE_BAR_LEFT_MARGIN,
            margins.top(),
            margins.right(),
            margins.bottom(),
        )

        super()._update_titlebar_layout()
