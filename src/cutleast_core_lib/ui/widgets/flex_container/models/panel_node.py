"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from cutleast_core_lib.core.utilities.pydantic_utils import include_literal_defaults


@include_literal_defaults
class PanelNode(BaseModel, frozen=True):
    """
    Leaf node of the layout tree representing a single docked panel.
    """

    type: Literal["panel"] = "panel"
    """Discriminator field; always `"panel"` for leaf nodes."""

    identifier: str
    """
    The persistent identifier returned by `FlexContent.get_identifier()` for the panel
    that occupies this slot.
    """
