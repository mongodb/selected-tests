"""CommitLimit class used to determine whether a commit is out of the desired range."""
from datetime import datetime
from typing import Optional

from git import Commit


class CommitLimit(object):
    """Represents the point in time at which to start analyzing commits of an evergreen project."""

    def __init__(
        self, stop_at_date: Optional[datetime] = None, stop_at_commit_sha: Optional[str] = None
    ):
        """
        Create a CommitLimit object.

        :param stop_at_date: The date at which to start analyzing commits of the repo.
        :param stop_at_commit_sha: The commit at which to start analyzing commits of the repo.
        """
        self.stop_at_date = stop_at_date
        self.stop_at_commit_sha = stop_at_commit_sha

    def __repr__(self) -> str:
        """Return the object representation of CommitLimit."""
        return f"CommitLimit({self.stop_at_date}, {self.stop_at_commit_sha})"

    def check_commit_before_limit(self, commit: Commit) -> bool:
        """
        Check whether a commit comes before the limit set by stop_at_date or stop_at_commit_sha.

        :param commit: The commit to compare against.
        :return: Whether or not the commit comes before the limit.
        """
        if self.stop_at_date:
            if commit.committed_datetime < self.stop_at_date:
                return True
        else:
            if commit.hexsha == self.stop_at_commit_sha:
                return True
        return False
