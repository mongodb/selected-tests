"""CommitLimit class used to determine whether a commit is out of the desired range."""
from git import Commit
from typing import Optional
from datetime import datetime


class CommitLimit(object):
    """Represents the point in time at which to start analyzing commits of an evergreen project."""

    def __init__(
        self, after_date: Optional[datetime] = None, after_commit_sha: Optional[str] = None
    ):
        """
        Create a CommitLimit object.

        :param after_date: The date at which to start analyzing commits of the repo.
        :param after_commit_sha: The commit at which to start analyzing commits of the repo.
        """
        self.after_date = after_date
        self.after_commit_sha = after_commit_sha

    def check_commit_before_limit(self, commit: Commit) -> bool:
        """
        Check whether a commit comes before the limit set by after_date or after_commit_sha.

        :param commit: The commit to compare against.
        :return: Whether or not the commit comes before the limit.
        """
        if self.after_date:
            if commit.committed_datetime < self.after_date:
                return True
        else:
            if commit.hexsha == self.after_commit_sha:
                return True
        return False
