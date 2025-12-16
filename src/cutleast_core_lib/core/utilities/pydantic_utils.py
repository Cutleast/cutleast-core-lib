"""
Copyright (c) Cutleast
"""

from typing import Any, Literal, TypeVar, get_origin

from pydantic import SerializerFunctionWrapHandler, model_serializer
from pydantic.main import BaseModel

ModelType = TypeVar("ModelType", bound=type[BaseModel])


def include_literal_defaults(cls: ModelType) -> ModelType:
    """
    Decorator that forces Literal-annotated fields to be included in serialization,
    even when `exclude_defaults=True` is used.
    """

    # this dynamic wrapper class is required in order to set the model serializer before
    # Pydantic builds the model
    class WrappedModel(cls):
        @model_serializer(mode="wrap")
        def _serialize_literals(
            self, next_serializer: SerializerFunctionWrapHandler
        ) -> dict[str, Any]:
            dumped: dict[str, Any] = next_serializer(self)

            for name, field_info in cls.model_fields.items():
                if get_origin(field_info.annotation) is Literal:
                    if name not in dumped:
                        dumped[name] = getattr(self, name)

            return dumped

    # copy metadata so that the class name in the traceback/debugger is correct
    WrappedModel.__name__ = cls.__name__
    WrappedModel.__qualname__ = cls.__qualname__
    WrappedModel.__doc__ = cls.__doc__

    return WrappedModel  # pyright: ignore[reportReturnType]
