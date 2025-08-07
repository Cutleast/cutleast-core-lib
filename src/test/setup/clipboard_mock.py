"""
Copyright (c) Cutleast
"""


class ClipboardMock:
    """
    Mocked clipboard for ui-related tests.

    Use in a Pytest fixture like this:
    ```
    clipboard_mock = ClipboardMock()

    monkeypatch.setattr("PySide6.QtGui.QClipboard.setText", clipboard_mock.copy)
    monkeypatch.setattr("PySide6.QtGui.QClipboard.text", clipboard_mock.paste)

    yield clipboard_mock
    ```
    """

    __content: str = ""

    def copy(self, text: str) -> None:
        self.__content = text

    def paste(self) -> str:
        return self.__content
