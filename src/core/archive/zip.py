"""
Copyright (c) Cutleast
"""

import zipfile
from typing import Optional, override

from .archive import Archive


class ZIPARchive(Archive):
    """
    Class for ZIP Archives.
    """

    __files: Optional[list[str]] = None

    @property
    @override
    def files(self) -> list[str]:
        if self.__files is None:
            self.__files = [
                file.filename
                for file in zipfile.ZipFile(self.path).filelist
                if not file.is_dir()
            ]

        return self.__files
