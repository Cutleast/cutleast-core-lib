"""
Copyright (c) Cutleast
"""

from pydantic import BaseModel, ConfigDict


class ThemeModel(BaseModel):
    """
    Base model for immutable theme tokens.
    """

    # config dict instead of class header attributes to also apply to subclasses
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_by_name=True,
        validate_by_alias=True,
        arbitrary_types_allowed=True,
    )
