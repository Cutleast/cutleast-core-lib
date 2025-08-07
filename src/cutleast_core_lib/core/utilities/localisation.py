"""
Copyright (c) Cutleast
"""

import locale
import logging
from typing import Optional

import win32api

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
        language_id: int = win32api.GetUserDefaultLangID()
        system_locale = locale.windows_locale[language_id]
        log.debug(f"Detected system language: {system_locale}")

    except Exception as ex:
        log.error(f"Failed to get system language: {ex}", exc_info=ex)

    return system_locale
