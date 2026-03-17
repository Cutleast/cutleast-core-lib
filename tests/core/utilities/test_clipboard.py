"""
Copyright (c) Cutleast
"""

from typing import Generator, Optional, cast

import pytest
from cutleast_core_lib.core.utilities.clipboard import Clipboard
from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.setup.clipboard_mock import ClipboardMock
from pydantic import BaseModel
from PySide6.QtCore import QMimeData


class _SampleModel(BaseModel):
    """Simple pydantic model used as test fixture data."""

    name: str
    """A name string."""

    value: int
    """An integer value."""


class _OtherModel(BaseModel):
    """Second pydantic model to test type mismatch scenarios."""

    label: str
    """A label string."""


class TestClipboard(BaseTest):
    """
    Tests `cutleast_core_lib.core.utilities.clipboard.Clipboard`.
    """

    DEFAULT_MIME_TYPE: str = "application/x-cutleast-core-lib+json"
    """The default MIME type used by `Clipboard`."""

    @pytest.fixture(autouse=True)
    def reset_mime_type(self) -> Generator[None, None, None]:
        """
        Resets the Clipboard MIME type to its default value after each test
        to prevent state leakage between tests.
        """

        yield
        Clipboard.set_mime_type(TestClipboard.DEFAULT_MIME_TYPE)

    def test_copy_sets_mime_data_on_clipboard(self, clipboard: ClipboardMock) -> None:
        """
        Tests that `copy` serialises the object and places it on the clipboard.
        """

        # given
        obj = _SampleModel(name="hello", value=42)

        # when
        Clipboard.copy(obj)
        mime_data: Optional[QMimeData] = clipboard.mimeData()

        # then
        assert mime_data is not None
        assert mime_data.hasFormat(TestClipboard.DEFAULT_MIME_TYPE)

    def test_copy_encodes_correct_type_name(self, clipboard: ClipboardMock) -> None:
        """
        Tests that the payload written by `copy` contains the correct type name.
        """

        # given
        obj = _SampleModel(name="test", value=1)

        # when
        Clipboard.copy(obj)
        mime_data: Optional[QMimeData] = clipboard.mimeData()

        # then
        assert mime_data is not None

        # when
        raw: bytes = cast(bytes, mime_data.data(TestClipboard.DEFAULT_MIME_TYPE).data())
        payload: Clipboard.ClipboardPayload = (
            Clipboard.ClipboardPayload.model_validate_json(raw)
        )

        # then
        assert payload.type == _SampleModel.__qualname__

    def test_copy_encodes_correct_data(self, clipboard: ClipboardMock) -> None:
        """
        Tests that the payload written by `copy` contains the correct JSON data.
        """

        # given
        obj = _SampleModel(name="lol", value=99)

        # when
        Clipboard.copy(obj)
        mime_data: Optional[QMimeData] = clipboard.mimeData()

        # then
        assert mime_data is not None

        # when
        raw: bytes = cast(bytes, mime_data.data(TestClipboard.DEFAULT_MIME_TYPE).data())
        payload: Clipboard.ClipboardPayload = (
            Clipboard.ClipboardPayload.model_validate_json(raw)
        )
        restored: _SampleModel = _SampleModel.model_validate_json(payload.data)

        # then
        assert restored == obj

    def test_contains_valid_obj_returns_true_for_matching_type(
        self, clipboard: ClipboardMock
    ) -> None:
        """
        Tests that `contains_valid_obj` returns `True` when the clipboard holds an object
        of the expected type.
        """

        # given
        obj = _SampleModel(name="x", value=0)
        Clipboard.copy(obj)

        # when
        result: bool = Clipboard.contains_valid_obj(_SampleModel)

        # then
        assert result is True

    def test_contains_valid_obj_returns_false_for_wrong_type(
        self, clipboard: ClipboardMock
    ) -> None:
        """
        Tests that `contains_valid_obj` returns `False` when the clipboard holds an
        object of a different type.
        """

        # given
        obj = _SampleModel(name="x", value=0)
        Clipboard.copy(obj)

        # when
        result: bool = Clipboard.contains_valid_obj(_OtherModel)

        # then
        assert result is False

    def test_contains_valid_obj_returns_false_for_empty_clipboard(
        self, clipboard: ClipboardMock
    ) -> None:
        """
        Tests that `contains_valid_obj` returns `False` when the clipboard is empty.
        """

        # when
        result = Clipboard.contains_valid_obj(_SampleModel)

        # then
        assert result is False

    def test_paste_returns_correct_object(self, clipboard: ClipboardMock) -> None:
        """
        Tests that `paste` deserialises and returns the correct object.
        """

        # given
        obj = _SampleModel(name="loremipsum", value=7)
        Clipboard.copy(obj)

        # when
        result: _SampleModel = Clipboard.paste(_SampleModel)

        # then
        assert result == obj

    def test_paste_raises_if_clipboard_is_empty(self, clipboard: ClipboardMock) -> None:
        """
        Tests that `paste` raises `ValueError` when the clipboard contains no data with
        the expected MIME type.
        """

        # when / then
        with pytest.raises(ValueError):
            Clipboard.paste(_SampleModel)

    def test_paste_raises_if_type_mismatch(self, clipboard: ClipboardMock) -> None:
        """
        Tests that `paste` raises `ValueError` when the clipboard contains an object of a
        different type than requested.
        """

        # given
        obj = _SampleModel(name="mismatch", value=3)
        Clipboard.copy(obj)

        # when / then
        with pytest.raises(ValueError):
            Clipboard.paste(_OtherModel)

    def test_set_mime_type_changes_used_mime_type(
        self, clipboard: ClipboardMock
    ) -> None:
        """
        Tests that `set_mime_type` causes `copy` and `contains_valid_obj` to use the new
        MIME type.
        """

        # given
        custom_mime = "application/x-custom-test"
        Clipboard.set_mime_type(custom_mime)
        obj = _SampleModel(name="mime", value=5)

        # when
        Clipboard.copy(obj)
        mime_data: Optional[QMimeData] = clipboard.mimeData()

        # then
        assert mime_data is not None
        assert mime_data.hasFormat(custom_mime)
        assert not mime_data.hasFormat(TestClipboard.DEFAULT_MIME_TYPE)

    def test_set_mime_type_affects_contains_valid_obj(
        self, clipboard: ClipboardMock
    ) -> None:
        """
        Tests that `contains_valid_obj` uses the updated MIME type set via
        `set_mime_type`.
        """

        # given
        custom_mime = "application/x-custom-test"
        obj = _SampleModel(name="mime", value=5)
        Clipboard.copy(obj)  # written with default MIME type

        # when
        Clipboard.set_mime_type(custom_mime)
        result: bool = Clipboard.contains_valid_obj(_SampleModel)

        # then
        assert result is False  # old data not found under new MIME type

    def test_paste_roundtrip_preserves_all_fields(
        self, clipboard: ClipboardMock
    ) -> None:
        """
        Tests that a full copy-paste roundtrip preserves all fields of the object
        exactly.
        """

        # given
        obj = _SampleModel(name="roundtrip", value=1234)

        # when
        Clipboard.copy(obj)
        result: _SampleModel = Clipboard.paste(_SampleModel)

        # then
        assert result.name == obj.name
        assert result.value == obj.value
