"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from typing import Any, Callable, ClassVar, Iterator, ParamSpec, TypeVar, override

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

DYNAMIC: Any = object()
"""
Use this as a dummy default value for `Field(default=DYNAMIC, ...)` when fully relying on
the `@default_factory(...)` decorator.
"""

P = ParamSpec("P")
R = TypeVar("R")
V = TypeVar("V")


def default_factory(
    field_name: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator that marks a (class) method as the default factory for a specific field.
    The model must subclass `DynamicDefaultModel`.

    Important for decorator order:
    `@default_factory(...)` should be placed *above* `@classmethod` so that
    `default_factory` receives the result of `@classmethod` (a classmethod object) and
    can mark it.

    Args:
        field_name (str): Name of the field whose `default_factory` should be replaced.

    Returns:
        Callable[P, R]: The unmodified (possibly classmethod) callable, but marked.
    """

    def _wrap(func: Callable[P, R]) -> Callable[P, R]:
        # Mark the object (even if it is already a classmethod).
        setattr(func, "__is_dynamic_default_factory__", True)
        setattr(func, "__dynamic_default_field__", field_name)
        return func

    return _wrap


class DynamicDefaultModel(BaseModel):
    """
    Base class that supports dynamic default factories via decorator.
    Subclasses can override default factories; the values are still considered
    "not explicitly set" by Pydantic (exclude_unset=True).
    """

    # Per class: Mapping from field name -> (classmethod/callable-marked) factory
    __dynamic_default_factories__: ClassVar[dict[str, Callable[[], Any]]] = {}

    @classmethod
    def __iter_marked_factories__(cls) -> Iterator[tuple[str, Callable[..., Any]]]:
        """
        Collects all callables in this class that are marked via decorator.
        Yields (field_name, callable) pairs.
        """

        for _, obj in cls.__dict__.items():
            field_name = getattr(obj, "__dynamic_default_field__", None)
            is_marked = getattr(obj, "__is_dynamic_default_factory__", False)
            if is_marked and isinstance(field_name, str):
                yield field_name, obj  # obj can be a function OR a classmethod

    @classmethod
    def __bind_factory_to_class__(
        cls, factory_obj: Callable[..., Any]
    ) -> Callable[[], Any]:
        """
        Converts a (possibly classmethod) object into a zero-argument factory
        as expected by pydantic.Field.default_factory.
        """

        # If it is a classmethod object, bind it correctly to the class
        if isinstance(factory_obj, classmethod):

            def _zero_arg() -> Any:
                bound = factory_obj.__get__(None, cls)
                return bound()

            return _zero_arg

        # Regular callable without parameters
        def _zero_arg() -> Any:
            return factory_obj()

        return _zero_arg

    @override
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        When creating each subclass:
        - Inherit the mapping of dynamic default factories along the MRO
        - Override with the factories marked in *this* class
        - Apply the resulting factories to the Pydantic fields
        - Rebuild the model to keep schema & validation consistent
        """

        super().__pydantic_init_subclass__(**kwargs)

        # 1) Inherit: build from base classes (from higher up to closer down)
        mapping: dict[str, Callable[..., Any]] = {}
        for base in reversed(
            cls.__mro__[1:]
        ):  # from higher up in MRO to nearer classes
            base_map = getattr(base, "__dynamic_default_factories__", None)
            if isinstance(base_map, dict):
                mapping.update(base_map)

        # 2) Collect own marked factories in this class (override)
        for field_name, factory_obj in cls.__iter_marked_factories__():
            mapping[field_name] = factory_obj

        # 3) Attach mapping to this class (so further subclasses inherit/override it)
        cls.__dynamic_default_factories__ = mapping

        # 4) Apply to Pydantic fields (only if the field exists)
        model_fields = getattr(cls, "model_fields", {})
        for field_name, factory_obj in mapping.items():
            if field_name not in model_fields:
                continue

            field: FieldInfo = model_fields[field_name]

            # Set default_factory; important: set default to PydanticUndefined
            # so that the field is considered "unset" when the user doesn't provide a value.
            field.default_factory = cls.__bind_factory_to_class__(factory_obj)
            field.default = PydanticUndefined

        # 5) Rebuild the model to keep everything consistent (schema, validation, caches)
        # force=True because we modified fields at a low level.
        cls.model_rebuild(force=True)
