"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.core.utilities.qt_res_provider import read_resource

from .models.theme import Theme
from .models.types import TOKEN_PATTERN


class StyleSheetRenderer:
    """
    Class for rendering the full style sheet by reading the raw QSS files and
    substituting the variables defined in the theme configuration.
    """

    @staticmethod
    def render(qss_resources: list[str], theme: Theme) -> str:
        """
        Renders the full style sheet by reading the raw QSS files and substituting
        the variables defined in the theme configuration.

        Args:
            qss_resources (list[str]): List of QSS resources to render.
            theme (Theme): Theme containing the variables for substitution.

        Raises:
            FileNotFoundError: If one of the resources does not exist.

        Returns:
            str: The rendered style sheet, ready to be applied to the QApplication.
        """

        qss_content: str = ""
        for resource in qss_resources:
            qss_content += f"\n/* {resource} */\n"
            qss_content += read_resource(resource)
            qss_content += f"\n/* {'-' * len(resource)} */\n"

        qss_content = qss_content.strip("\n")
        qss_content = TOKEN_PATTERN.sub(
            lambda match: theme.resolve(match.group()), qss_content
        )

        return qss_content
