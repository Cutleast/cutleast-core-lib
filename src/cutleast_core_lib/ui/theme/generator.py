"""
Copyright (c) Cutleast
"""

from typing import Any, cast

from cutleast_core_lib.core.utilities.qt_res_provider import load_json_resource

from .models.definition import ThemeDefinition
from .models.theme import Theme
from .models.types import HexColorStr


class ThemeGenerator:
    """
    Class for generating a complete theme based on a base theme and project-specific
    overrides.
    """

    @staticmethod
    def generate(theme_resources: list[str], primary_color: HexColorStr) -> Theme:
        """
        Generates a theme from layered JSON resources and a primary color.

        Args:
            theme_resources (list[str]):
                List of JSON resources containing (partial) theme definitions.
            primary_color (HexColorStr): Primary color used to complete the theme.

        Raises:
            FileNotFoundError: If one of the resources does not exist.
            TypeError: If one of the resources does not contain a JSON object.
            ValueError: If JSON parsing or theme validation fails.

        Returns:
            Theme: The generated and validated theme.
        """

        theme_data: dict[str, Any] = {}
        for resource in theme_resources:
            theme_data = ThemeGenerator.__merge(
                theme_data, ThemeGenerator.__load_resource(resource)
            )

        definition: ThemeDefinition = ThemeDefinition.model_validate(theme_data)

        return Theme.from_definition(definition, primary_color)

    @staticmethod
    def __load_resource(resource: str) -> dict[str, Any]:
        """
        Loads a theme definition from a JSON resource.

        Args:
            resource (str): Resource containing the theme definition.

        Raises:
            FileNotFoundError: If the resource does not exist.
            TypeError: If the resource does not contain a JSON object.
            ValueError: If JSON parsing fails.

        Returns:
            dict[str, Any]: Loaded theme definition data.
        """

        data: Any = load_json_resource(resource)
        if not isinstance(data, dict):
            raise TypeError(
                f"Theme definition resource '{resource}' must contain a JSON object."
            )

        return cast(dict[str, Any], data)

    @staticmethod
    def __merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively merges overrides into base theme data without mutating either input.

        Args:
            base (dict[str, Any]): Base theme data.
            overrides (dict[str, Any]): Higher-priority theme data.

        Returns:
            dict[str, Any]: Recursively merged theme data.
        """

        merged: dict[str, Any] = base.copy()

        for key, override_value in overrides.items():
            base_value: Any = merged.get(key)
            if isinstance(base_value, dict) and isinstance(override_value, dict):
                merged[key] = ThemeGenerator.__merge(base_value, override_value)
            else:
                merged[key] = override_value

        return merged
