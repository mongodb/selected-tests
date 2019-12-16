from unittest.mock import patch, MagicMock

import selectedtests.datasource.mongo_wrapper as under_test


NS = "selectedtests.datasource.mongo_wrapper"


def ns(relative_name):  # pylint: disable=invalid-name
    """Return a full name from a name relative to the test module"s name space."""
    return NS + "." + relative_name


class TestMongoWrapper:
    @patch(ns("MongoClient"))
    def test_mongo_wrapper_wraps_mongo_client(self, mongo_mock):
        mongo_wrapper = under_test.MongoWrapper.connect("mongo_uri")

        assert mongo_wrapper.client == mongo_mock.return_value

    def test_getting_test_mappings_queue_collection(self):
        client_mock = MagicMock()

        wrapper = under_test.MongoWrapper(client_mock)

        assert client_mock.selected_tests.test_mappings_queue == wrapper.test_mappings_queue()

    def test_getting_task_mappings_queue_collection(self):
        client_mock = MagicMock()

        wrapper = under_test.MongoWrapper(client_mock)

        assert client_mock.selected_tests.task_mappings_queue == wrapper.task_mappings_queue()

    def test_getting_task_mappings_collection(self):
        client_mock = MagicMock()

        wrapper = under_test.MongoWrapper(client_mock)

        assert client_mock.selected_tests.task_mappings == wrapper.task_mappings()

    def test_getting_test_mappings_collection(self):
        client_mock = MagicMock()

        wrapper = under_test.MongoWrapper(client_mock)

        assert client_mock.selected_tests.test_mappings == wrapper.test_mappings()

    def test_getting_project_config_collection(self):
        client_mock = MagicMock()

        wrapper = under_test.MongoWrapper(client_mock)

        assert client_mock.selected_tests.project_config == wrapper.project_config()
