import selectedtests.helpers as under_test

NS = "selectedtests.evergreen_helper"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestCreateQuery:
    def test_no_mutable_joined(self):
        query = under_test.create_query({"imput": 1})
        assert query == {"imput": 1}

    def test_mutable_and_joined(self):
        query = under_test.create_query(
            {"imput": 1, "flip_count": 2, "tests": 3},
            mutable=["flip_count", "source_file_seen_count"],
            joined=["tests", "tasks"],
        )
        assert query == {"imput": 1}
