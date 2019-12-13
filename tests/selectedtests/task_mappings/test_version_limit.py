from datetime import datetime, timedelta
from unittest.mock import MagicMock

from selectedtests.task_mappings import version_limit as under_test


class TestCheckVersionBeforeLimit:
    def test_when_version_date_is_before_limit_date(self):
        now = datetime.utcnow()
        two_days_ago = now - timedelta(days=2)
        version_mock = MagicMock(version_id="version", create_time=two_days_ago)
        version_limit = under_test.VersionLimit(stop_at_date=now)

        assert version_limit.check_version_before_limit(version_mock)

    def test_when_version_date_is_after_limit_date(self):
        now = datetime.utcnow()
        two_days_ago = now - timedelta(days=2)
        version_mock = MagicMock(version_id="version", create_time=now)
        version_limit = under_test.VersionLimit(stop_at_date=two_days_ago)

        assert not version_limit.check_version_before_limit(version_mock)

    def test_when_version_id_equals_stop_at_version_id(self):
        version_mock = MagicMock(version_id="my-version", create_time=datetime.utcnow())
        version_limit = under_test.VersionLimit(stop_at_version_id="my-version")

        assert version_limit.check_version_before_limit(version_mock)

    def test_when_version_id_does_not_equal_stop_at_version_id(self):
        version_mock = MagicMock(version_id="my-version", create_time=datetime.utcnow())
        version_limit = under_test.VersionLimit(stop_at_version_id="other-version")

        assert not version_limit.check_version_before_limit(version_mock)
