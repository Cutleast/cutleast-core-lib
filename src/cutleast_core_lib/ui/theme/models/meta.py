"""
Copyright (c) Cutleast
"""


class MetaAttributes(dict[str, str]):
    """
    A dictionary of meta attributes for a theme, where each key is a string and each
    value is a string.
    """

    def __getattr__(self, name: str, /) -> str:
        """
        Returns the value of an attribute-style dictionary entry.

        Args:
            name (str): Name of the requested entry.

        Raises:
            AttributeError: If the requested entry does not exist.

        Returns:
            str: Value of the requested entry.
        """

        try:
            return self[name]
        except KeyError as ex:
            raise AttributeError(name) from ex
