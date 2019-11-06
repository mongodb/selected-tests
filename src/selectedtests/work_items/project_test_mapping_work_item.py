"""Model of Evergreen TestMapping that needs to be analyzed."""
import structlog

from datetime import datetime, timedelta
from pymongo.errors import DuplicateKeyError
from pymongo.collection import Collection, ReturnDocument

LOGGER = structlog.get_logger()
WORK_ITEM_TTL = timedelta(weeks=2).total_seconds()


class ProjectTestMappingWorkItem(object):
    """A work item for an evergreen test_mapping."""

    def __init__(
        self,
        start_time,
        end_time,
        created_on: datetime,
        project: str,
        source_file_regex: str,
        test_file_regex: str,
        module: str,
        module_source_file_regex: str,
        module_test_file_regex: str,
    ):
        """
        Create a test_mapping work item.

        :param start_time: Time work was started on item.
        :param end_time: Time work completed on item.
        :param created_on: Time work item was created.
        :param project: The name of the evergreen project to analyze.
        :param source_file_regex: Regex pattern to match changed source files against.
        :param test_file_regex: Regex pattern to match changed test files against.
        :param module: The name of the module to analyze.
        :param module_source_file_regex: Regex pattern to match changed module source files against.
        :param module_test_file_regex: Regex pattern to match changed module test files against.
        """
        self.start_time = start_time
        self.end_time = end_time
        self.created_on = created_on
        self.project = project
        self.source_file_regex = source_file_regex
        self.test_file_regex = test_file_regex
        self.module = module
        self.module_source_file_regex = module_source_file_regex
        self.module_test_file_regex = module_test_file_regex

    @classmethod
    def new_test_mappings(
        cls,
        project: str,
        source_file_regex: str,
        test_file_regex: str,
        module: str = "",
        module_source_file_regex: str = "",
        module_test_file_regex: str = "",
    ):
        """
        Create a new work item.

        :param project: The name of the evergreen project to analyze.
        :param source_file_regex: Regex pattern to match changed source files against.
        :param test_file_regex: Regex pattern to match changed test files against.
        :param module: The name of the module to analyze.
        :param module_source_file_regex: Regex pattern to match changed module source files against.
        :param module_test_file_regex: Regex pattern to match changed module test files against.
        :return: ProjectTestMappingWorkItem instance for work item.
        """
        return cls(
            None,
            None,
            datetime.utcnow(),
            project,
            source_file_regex,
            test_file_regex,
            module,
            module_source_file_regex,
            module_test_file_regex,
        )

    @classmethod
    def next(cls, collection: Collection):
        """
        Find a Work Item on the queue ready for work, or None if nothing is ready.

        :param collection: Mongo collection where queue is found.
        :return: Work item ready for work, or None.
        """
        data = collection.find_one_and_update(
            {"start_time": None},
            {"$currentDate": {"start_time": True}},
            sort=[("created_on", 1)],
            return_document=ReturnDocument.AFTER,
        )
        if data:
            return cls(
                data.get("start_time", None),
                data.get("end_time", None),
                data["created_on"],
                data["project"],
                data["source_file_regex"],
                data["test_file_regex"],
                data["module"],
                data["module_source_file_regex"],
                data["module_test_file_regex"],
            )
        return None

    def insert(self, collection: Collection):
        """
        Add this work item to the Mongo collection.

        If this work item already exists, just update the created_on timestamp.

        :param collection: Mongo collection containing queue.
        :return: True if item was new record was added to collection.
        """
        LOGGER.info("Adding new test_mapping work item for project", project=self.project)
        try:
            result = collection.insert_one(
                {
                    "created_on": self.created_on,
                    "project": self.project,
                    "source_file_regex": self.source_file_regex,
                    "test_file_regex": self.test_file_regex,
                    "module": self.module,
                    "module_source_file_regex": self.module_source_file_regex,
                    "module_test_file_regex": self.module_test_file_regex,
                }
            )
            return result.acknowledged
        except DuplicateKeyError:
            return False

    def complete(self, collection: Collection):
        """
        Mark this work item as complete.

        :param collection: Mongo collection containing queue.
        """
        collection.update_one({"project": self.project}, {"$currentDate": {"end_time": True}})
