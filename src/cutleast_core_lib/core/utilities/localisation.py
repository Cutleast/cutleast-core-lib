"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

from PySide6.QtCore import QLocale

log: logging.Logger = logging.getLogger("Localisation")


def detect_system_locale() -> Optional[str]:
    """
    Attempts to detect the system locale.

    Returns:
        str: System locale
    """

    log.info("Detecting system locale...")

    system_locale: Optional[str] = None

    try:
        system_locale = (
            f"{QLocale.languageToCode(QLocale.system().language())}_"
            f"{QLocale.territoryToCode(QLocale.system().territory())}"
        )
        log.debug(f"Detected system language: {system_locale}")

    except Exception as ex:
        log.error(f"Failed to get system language: {ex}", exc_info=ex)

    return system_locale
