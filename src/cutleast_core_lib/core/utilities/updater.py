"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

import jstyleson as json
import requests
import semantic_version as semver

from cutleast_core_lib.ui.widgets.updater_dialog import UpdaterDialog

from .exceptions import format_exception
from .singleton import Singleton
from .web_utils import get_raw_web_content_uncached


class Updater(Singleton):
    """
    Class for updating application.
    """

    log: logging.Logger = logging.getLogger("Updater")

    repo_name: str
    repo_branch: str
    repo_owner: str
    changelog_url: str
    update_url: str

    installed_version: semver.Version
    latest_version: Optional[semver.Version] = None
    download_url: str

    def __init__(
        self, repo_name: str, repo_branch: str, repo_owner: str, installed_version: str
    ) -> None:
        """
        Args:
            repo_name (str): Name of the project repository.
            repo_branch (str): Branch of the project repository.
            repo_owner (str): Owner of the project repository.
            installed_version (str): Installed version of the application.
        """

        super().__init__()

        self.repo_name = repo_name
        self.repo_branch = repo_branch
        self.repo_owner = repo_owner
        self.changelog_url = (
            f"https://raw.githubusercontent.com/{self.repo_owner}/"
            f"{self.repo_name}/{self.repo_branch}/Changelog.md"
        )
        self.update_url = (
            f"https://raw.githubusercontent.com/{self.repo_owner}/"
            f"{self.repo_name}/{self.repo_branch}/update.json"
        )
        self.installed_version = semver.Version(installed_version)

    def run(self) -> None:
        """
        Checks for updates and runs dialog.
        """

        self.log.info("Checking for update...")

        if self.is_update_available():
            self.log.info(
                f"Update available: Installed: {self.installed_version} - Latest: "
                f"{self.latest_version}"
            )

            UpdaterDialog(
                self.installed_version,
                self.latest_version,  # type: ignore
                self.get_changelog(),
                self.download_url,
            )
        else:
            self.log.info("No update available.")

    def is_update_available(self) -> bool:
        """
        Checks if an update is available to download.

        Returns:
            bool: `True` if an update is available, `False` otherwise.
        """

        self.__request_update()

        if self.latest_version is None:
            return False

        update_available: bool = self.installed_version < self.latest_version
        return update_available

    def __request_update(self) -> None:
        """
        Requests latest available version and download url from GitHub repository.
        """

        try:
            response = get_raw_web_content_uncached(self.update_url)

            latest_version_json: str = response.decode(encoding="utf8", errors="ignore")
            latest_version_data: dict[str, str] = json.loads(latest_version_json)
            latest_version: str = latest_version_data["version"]
            self.latest_version = semver.Version(latest_version)
            self.download_url = latest_version_data["download_url"]

        except requests.exceptions.RequestException as ex:
            self.log.error(f"Failed to request update: {ex}")
            self.log.debug(f"Request URL: {self.update_url}")

    def get_changelog(self) -> str:
        """
        Gets changelog from repository.

        Returns:
            str: Changelog as Markdown or error message.
        """

        try:
            return get_raw_web_content_uncached(self.changelog_url).decode("utf-8")
        except Exception as ex:
            return format_exception(ex)
