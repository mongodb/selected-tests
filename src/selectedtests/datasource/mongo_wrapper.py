"""Classes for accessing mongo collections."""
from pymongo import MongoClient
from pymongo.collection import Collection


class MongoWrapper(object):
    """Wrapper for MongoClient."""

    def __init__(self, mongo_client: MongoClient):
        """
        Create wrapper for given client.

        :param mongo_client: Client to wrap.
        """
        self.client = mongo_client

    @classmethod
    def connect(cls, mongo_uri: str):
        """
        Create wrapper for mongo client to given mongo URI.

        :param mongo_uri: Mongo URI to connect to.
        :return: MongoWrapper for given URI.
        """
        client = MongoClient(mongo_uri)
        return cls(client)

    def test_mappings_queue(self) -> Collection:
        """
        Get 'test_mappings_queue' collection on selected_tests database.

        :return: test_mappings_queue collection.
        """
        return self.client.selected_tests.test_mappings_queue

    def task_mappings_queue(self) -> Collection:
        """
        Get 'task_mappings_queue' collection on selected_tests database.

        :return: task_mappings_queue collection.
        """
        return self.client.selected_tests.task_mappings_queue

    def test_mappings(self) -> Collection:
        """
        Get 'test_mappings' collection on selected_tests database.

        :return: test_mappings collection.
        """
        return self.client.selected_tests.test_mappings

    def task_mappings(self) -> Collection:
        """
        Get 'task_mappings' collection on selected_tests database.

        :return: task_mappings collection.
        """
        return self.client.selected_tests.task_mappings

    def project_config(self) -> Collection:
        """
        Get 'project_config' collection on selected_tests database.

        :return: project_config collection.
        """
        return self.client.selected_tests.project_config
