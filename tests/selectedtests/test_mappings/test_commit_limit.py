import git
import pytz

from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

from selectedtests.test_mappings import commit_limit as under_test


class TestCheckCommitBeforeLimit:
    def test_when_commit_date_is_before_limit_date(self):
        with TemporaryDirectory() as tmpdir:
            repo = git.Repo.init(tmpdir)
            commit = repo.index.commit("initial commit -- no files changed")

            now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            two_days_from_now = now + timedelta(days=2)
            commit_limit = under_test.CommitLimit(after_date=two_days_from_now)

            assert commit_limit.check_commit_before_limit(commit)

    def test_when_commit_date_is_after_limit_date(self):
        with TemporaryDirectory() as tmpdir:
            repo = git.Repo.init(tmpdir)
            commit = repo.index.commit("initial commit -- no files changed")

            now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            two_days_ago = now - timedelta(days=2)
            commit_limit = under_test.CommitLimit(after_date=two_days_ago)

            assert not commit_limit.check_commit_before_limit(commit)

    def test_when_commit_sha_equals_after_commit_sha(self):
        with TemporaryDirectory() as tmpdir:
            repo = git.Repo.init(tmpdir)
            commit = repo.index.commit("initial commit -- no files changed")

            commit_limit = under_test.CommitLimit(after_commit_sha=commit.hexsha)

            assert commit_limit.check_commit_before_limit(commit)

    def test_when_commit_sha_does_not_equal_after_commit_sha(self):
        with TemporaryDirectory() as tmpdir:
            repo = git.Repo.init(tmpdir)
            commit = repo.index.commit("initial commit -- no files changed")

            commit_limit = under_test.CommitLimit(after_commit_sha="some-other-commit-sha")

            assert not commit_limit.check_commit_before_limit(commit)
