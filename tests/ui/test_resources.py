"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.ui import resources_rc
from cutleast_core_lib.ui.theme.generator import ThemeGenerator
from cutleast_core_lib.ui.theme.manager import ThemeManager
from PySide6.QtCore import QFile


class TestResources:
    """Tests the isolated core Qt resource namespace."""

    def test_core_resources_are_registered_under_the_core_prefix(self) -> None:
        """Tests that the compiled core QRC registers its expected resource paths."""

        # given
        resource_path: str = ":/core-lib/styles/base.qss"

        # when
        is_available: bool = QFile.exists(resource_path)

        # then
        assert resources_rc is not None
        assert is_available

    def test_legacy_global_core_resource_path_is_not_registered(self) -> None:
        """Tests that the old global core resource namespace is absent."""

        # given
        legacy_resource_path: str = ":/styles/base.qss"

        # when
        is_available: bool = QFile.exists(legacy_resource_path)

        # then
        assert not is_available

    def test_theme_icons_are_registered_under_the_core_prefix(self) -> None:
        """Tests that theme icon tokens resolve to registered core resources."""

        # given
        theme_resource_groups: list[list[str]] = [
            [
                *ThemeManager.CORE_BASE_THEME_FILES,
                *ThemeManager.CORE_DARK_THEME_FILES,
            ],
            [
                *ThemeManager.CORE_BASE_THEME_FILES,
                *ThemeManager.CORE_LIGHT_THEME_FILES,
            ],
        ]

        # when
        icon_paths: list[str] = [
            icon_path
            for theme_resources in theme_resource_groups
            for icon_path in ThemeGenerator.generate(
                theme_resources, "#ffffff"
            ).resources.values()
        ]

        # then
        assert icon_paths
        assert all(path.startswith(":/core-lib/icons/") for path in icon_paths)
        assert all(QFile.exists(path) for path in icon_paths)
