from typing import Optional
from datetime import datetime

from evergreen.api import Version


class VersionLimit(object):
    """Represents the point in time at which to start analyzing versions of an evergreen project."""

    def __init__(
        self, after_date: Optional[datetime] = None, after_version_id: Optional[str] = None
    ):
        self.after_date = after_date
        self.after_version_id = after_version_id

    def check_version_before_limit(self, version: Version):
        if self.after_date:
            if version.create_time < self.after_date:
                return True
        else:
            if version.version_id == self.after_version_id:
                return True
        return False
