"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Self

from pydantic import BaseModel, model_validator

from cutleast_core_lib.core.utilities.pydantic_utils import include_literal_defaults

if TYPE_CHECKING:
    from .types import LayoutNode


@include_literal_defaults
class SplitterNode(BaseModel, frozen=True):
    """
    Inner node of the layout tree representing a splitter container that holds two or
    more children arranged either horizontally or vertically.
    """

    type: Literal["splitter"] = "splitter"
    """Discriminator field; always `"splitter"` for inner nodes."""

    orientation: Literal["horizontal", "vertical"]
    """
    Orientation of the splitter.

    * `"horizontal"` - children are arranged side by side (left -> right).
    * `"vertical"`   - children are stacked (top -> bottom).
    """

    children: list["LayoutNode"]
    """
    Ordered list of child nodes.  Each entry is either a `PanelNode` or a nested
    `SplitterNode`.
    """

    sizes: list[int]
    """
    Pixel sizes of each child as reported by `QSplitter.sizes()` at the time the layout
    was captured. The list length must equal `len(children)`.
    """

    @model_validator(mode="after")
    def _validate_sizes_length(self) -> Self:
        """
        Validates that the length of the `sizes` list matches the number of
        children.  This is a Pydantic root validator that runs after the model
        is initialized.
        """

        if len(self.sizes) != len(self.children):
            raise ValueError(
                f"Length of sizes ({len(self.sizes)}) must match number of children"
                f" ({len(self.children)})"
            )

        return self
