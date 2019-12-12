"""VersionLimit class used to determine whether an Evergreen version is out of the desired range."""
from typing import Optional
from datetime import datetime

from evergreen.api import Version


class VersionLimit(object):
    """Represents the point in time at which to start analyzing versions of an evergreen project."""

    def __init__(
        self, stop_at_date: Optional[datetime] = None, stop_at_version_id: Optional[str] = None
    ):
        """
        Create a VersionLimit object.

        :param stop_at_date: The date at which to start analyzing versions of the repo.
        :param stop_at_version_id: The id of the version at which to start analyzing versions.
        """
        self.stop_at_date = stop_at_date
        self.stop_at_version_id = stop_at_version_id

    def check_version_before_limit(self, version: Version) -> bool:
        """
        Check whether a version comes before the limit set by stop_at_date or stop_at_version_id.

        :param version: The version to compare against.
        :return: Whether or not the version comes before the limit.
        """
        if self.stop_at_date:
            if version.create_time < self.stop_at_date:
                return True
        else:
            if version.version_id == self.stop_at_version_id:
                return True
        return False
