"""VersionLimit class used to determine whether an Evergreen version is out of the desired range."""
from typing import Optional
from datetime import datetime

from evergreen.api import Version


class VersionLimit(object):
    """Represents the point in time at which to start analyzing versions of an evergreen project."""

    def __init__(
        self, after_date: Optional[datetime] = None, after_version_id: Optional[str] = None
    ):
        """
        Create a VersionLimit object.

        :param after_date: The date at which to start analyzing versions of the repo.
        :param after_version_id: The id of the version at which to start analyzing versions.
        """
        self.after_date = after_date
        self.after_version_id = after_version_id

    def check_version_before_limit(self, version: Version) -> bool:
        """
        Check whether a version comes before the limit set by after_date or after_version_id.

        :param version: The version to compare against.
        :return: Whether or not the version comes before the limit.
        """
        if self.after_date:
            if version.create_time < self.after_date:
                return True
        else:
            if version.version_id == self.after_version_id:
                return True
        return False
