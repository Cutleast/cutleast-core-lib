"""
Copyright (c) Cutleast
"""

import pytest
from requests_mock import Mocker as RequestsMocker

from cutleast_core_lib.core.utilities.exceptions import Non200HttpError
from cutleast_core_lib.core.utilities.updater import Updater
from cutleast_core_lib.test.base_test import BaseTest
from cutleast_core_lib.test.utils import Utils


class TestUpdater(BaseTest):
    """
    Tests `core.utilities.updater.Updater`.
    """

    def test_is_update_available(self, requests_mock: RequestsMocker) -> None:
        """
        Tests `Updater.is_update_available`.
        """

        # given
        updater = Updater(
            repo_name="cutleast-core-lib",
            repo_branch="main",
            repo_owner="Cutleast",
            installed_version="0.0.1",
        )

        # mock response
        requests_mock.get(
            "https://raw.githubusercontent.com/Cutleast/cutleast-core-lib/main/update.json",
            status_code=404,
        )

        # when/then
        with pytest.raises(Non200HttpError):
            updater.is_update_available()

        assert requests_mock.call_count == 1

        # mock response
        requests_mock.get(
            "https://raw.githubusercontent.com/Cutleast/cutleast-core-lib/main/update.json",
            json={
                "version": "0.0.2",
                "download_url": "https://github.com/Cutleast/cutleast-core-lib/releases/download/0.0.2/cutleast-core-lib-0.0.2-py3-none-any.whl",
            },
        )

        # when
        result: bool = updater.is_update_available()

        # then
        assert result
        assert requests_mock.call_count == 2

        # mock response
        requests_mock.get(
            "https://raw.githubusercontent.com/Cutleast/cutleast-core-lib/main/update.json",
            json={
                "version": "0.0.1-beta-1",
                "download_url": "https://github.com/Cutleast/cutleast-core-lib/releases/download/0.0.2/cutleast-core-lib-0.0.2-py3-none-any.whl",
            },
        )

        # when
        result = updater.is_update_available()

        # then
        assert not result
        assert requests_mock.call_count == 3

        # cleanup
        Utils.reset_singleton(Updater)

    def test_get_changelog(self, requests_mock: RequestsMocker) -> None:
        """
        Tests `Updater.get_changelog`.
        """

        # given
        updater = Updater(
            repo_name="cutleast-core-lib",
            repo_branch="main",
            repo_owner="Cutleast",
            installed_version="0.0.1",
        )

        # mock response
        requests_mock.get(
            "https://raw.githubusercontent.com/Cutleast/cutleast-core-lib/main/Changelog.md",
            status_code=404,
        )

        # when
        result: str = updater.get_changelog()

        # then
        assert "failed with status code 404!" in result
        assert requests_mock.call_count == 1

        # mock response
        requests_mock.get(
            "https://raw.githubusercontent.com/Cutleast/cutleast-core-lib/main/Changelog.md",
            text="# Changelog\n\n## [0.0.2] - 2024-01-01\n- Added new feature\n\n## [0.0.1] - 2023-12-01\n- Initial release",
        )

        # when
        result = updater.get_changelog()

        # then
        assert "## [0.0.2] - 2024-01-01" in result
        assert "## [0.0.1] - 2023-12-01" in result
        assert requests_mock.call_count == 2

        # cleanup
        Utils.reset_singleton(Updater)
