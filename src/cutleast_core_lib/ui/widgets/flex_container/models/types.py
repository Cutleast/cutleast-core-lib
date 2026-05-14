"""
Copyright (c) Cutleast
"""

from typing import Annotated

from pydantic import Field

from .panel_node import PanelNode
from .splitter_node import SplitterNode

type LayoutNode = Annotated[PanelNode | SplitterNode, Field(discriminator="type")]

SplitterNode.model_rebuild()
