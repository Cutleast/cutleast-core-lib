"""
Copyright (c) Cutleast
"""

from unittest.mock import Mock

import pytest
from cutleast_core_lib.core.utilities.lazy import Lazy


class TestLazy:
    """
    Tests `cutleast_core_lib.core.utilities.lazy.Lazy`.
    """

    def test_value_invokes_supplier_once_and_caches_result(self) -> None:
        """
        Tests that the supplier is called only for the first value access.
        """

        # given
        supplier = Mock(return_value="value")
        lazy = Lazy(supplier)

        # when
        first_value: str = lazy.value
        second_value: str = lazy.value

        # then
        assert first_value == second_value == "value"
        supplier.assert_called_once_with()

    def test_from_value_creates_initialized_lazy(self) -> None:
        """
        Tests that a static value creates an initialized lazy instance.
        """

        # given / when
        lazy = Lazy.from_value("value")

        # then
        assert lazy.has_value
        assert lazy.value == "value"

    def test_value_setter_replaces_cached_value(self) -> None:
        """
        Tests that assigning a value replaces the cached supplier result.
        """

        # given
        lazy = Lazy(lambda: "first")
        assert lazy.value == "first"

        # when
        lazy.value = "second"

        # then
        assert lazy.value == "second"

    def test_reset_invokes_supplier_again(self) -> None:
        """
        Tests that reset clears the cached value.
        """

        # given
        supplier = Mock(side_effect=["first", "second"])
        lazy = Lazy(supplier)
        assert lazy.value == "first"

        # when
        lazy.reset()

        # then
        assert not lazy.has_value
        assert lazy.value == "second"
        assert supplier.call_count == 2

    def test_supplier_exception_is_not_cached(self) -> None:
        """
        Tests that a failed supplier can be retried on the next access.
        """

        # given
        supplier = Mock(side_effect=[RuntimeError("failure"), "value"])
        lazy = Lazy(supplier)

        # when / then
        with pytest.raises(RuntimeError, match="failure"):
            _ = lazy.value

        assert not lazy.has_value
        assert lazy.value == "value"
