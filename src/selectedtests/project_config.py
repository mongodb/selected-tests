"""Domain object representing project config."""
from __future__ import annotations
from typing import Dict, Optional

from pymongo.collection import Collection


class TaskConfig:
    """Represents the task mappings config for a project config."""

    def __init__(
        self,
        most_recent_version_analyzed: Optional[str] = None,
        source_file_regex: Optional[str] = None,
        build_variant_regex: Optional[str] = None,
        module: Optional[str] = None,
        module_source_file_regex: Optional[str] = None,
    ):
        """Init a TaskConfig instance. Use ProjectConfig.get rather than this directly."""
        self.most_recent_version_analyzed = most_recent_version_analyzed
        self.source_file_regex = source_file_regex
        self.build_variant_regex = build_variant_regex
        self.module = module
        self.module_source_file_regex = module_source_file_regex

    @classmethod
    def from_json(cls, json: Dict[str, Optional[str]]) -> TaskConfig:
        """
        Instantiate an instance of TaskConfig from json. Use ProjectConfig.get instead.

        :param json: Json representing project task config in database.
        :return: An instance of TaskConfig.
        """
        return cls(
            json.get("most_recent_version_analyzed"),
            json.get("source_file_regex"),
            json.get("build_variant_regex"),
            json.get("module"),
            json.get("module_source_file_regex"),
        )

    def update(
        self,
        most_recent_version_analyzed: Optional[str],
        source_file_regex: str,
        build_variant_regex: str,
        module: str,
        module_source_file_regex: str,
    ) -> None:
        """
        Update fields on an instance of TaskConfig.

        :param most_recent_version_analyzed: The most recent version analyzed of the project.
        :param source_file_regex: The source_file_regex of the project task config.
        :param build_variant_regex: The build_variant_regex of the project task config.
        :param module: The module of the project task config.
        :param module_source_file_regex: The module_source_file_regex of the project task config.
        """
        self.most_recent_version_analyzed = most_recent_version_analyzed
        self.source_file_regex = source_file_regex
        self.build_variant_regex = build_variant_regex
        self.module = module
        self.module_source_file_regex = module_source_file_regex

    def update_most_recent_version_analyzed(self, most_recent_version_analyzed: str) -> None:
        """
        Update most_recent_version_analyzed field on an instance of TaskConfig.

        :param most_recent_version_analyzed: The most recent version analyzed of the project.
        """
        self.most_recent_version_analyzed = most_recent_version_analyzed

    def as_dict(self) -> Dict[str, Optional[str]]:
        """Return fields to be stored in database."""
        return {
            "most_recent_version_analyzed": self.most_recent_version_analyzed,
            "source_file_regex": self.source_file_regex,
            "build_variant_regex": self.build_variant_regex,
            "module": self.module,
            "module_source_file_regex": self.module_source_file_regex,
        }


class TestConfig:
    """Represents the test mappings config for a project config."""

    def __init__(
        self,
        most_recent_project_commit_analyzed: str = None,
        source_file_regex: str = None,
        test_file_regex: str = None,
        module: str = None,
        most_recent_module_commit_analyzed: str = None,
        module_source_file_regex: str = None,
        module_test_file_regex: str = None,
    ):
        """Init a TestConfig instance. Use ProjectConfig.get rather than this directly."""
        self.most_recent_project_commit_analyzed = most_recent_project_commit_analyzed
        self.source_file_regex = source_file_regex
        self.test_file_regex = test_file_regex
        self.module = module
        self.most_recent_module_commit_analyzed = most_recent_module_commit_analyzed
        self.module_source_file_regex = module_source_file_regex
        self.module_test_file_regex = module_test_file_regex

    @classmethod
    def from_json(cls, json: Dict[str, Optional[str]]) -> TestConfig:
        """
        Instantiate an instance of TestConfig from json. Use ProjectConfig.get instead.

        :param json: Json representing project test config in database.
        :return: An instance of TestConfig.
        """
        return cls(
            json.get("most_recent_project_commit_analyzed"),
            json.get("source_file_regex"),
            json.get("test_file_regex"),
            json.get("module"),
            json.get("most_recent_module_commit_analyzed"),
            json.get("module_source_file_regex"),
            json.get("module_test_file_regex"),
        )

    def update(
        self,
        most_recent_project_commit_analyzed: str,
        source_file_regex: str,
        test_file_regex: str,
        module: str,
        most_recent_module_commit_analyzed: str,
        module_source_file_regex: str,
        module_test_file_regex: str,
    ) -> None:
        """
        Update fields on an instance of TestConfig.

        :param most_recent_project_commit_analyzed: M. recent project commit analyzed of the config.
        :param source_file_regex: The source_file_regex of the project task config.
        :param test_file_regex: The test_file_regex of the project task config.
        :param module: The module of the project task config.
        :param most_recent_module_commit_analyzed: Most_recent_module_commit_analyzed of the config.
        :param module_source_file_regex: The module_source_file_regex of the project task config.
        :param module_test_file_regex: The module_test_file_regex of the project task config.
        """
        self.most_recent_project_commit_analyzed = most_recent_project_commit_analyzed
        self.source_file_regex = source_file_regex
        self.test_file_regex = test_file_regex
        self.module = module
        self.most_recent_module_commit_analyzed = most_recent_module_commit_analyzed
        self.module_source_file_regex = module_source_file_regex
        self.module_test_file_regex = module_test_file_regex

    def update_most_recent_commits_analyzed(
        self, most_recent_project_commit_analyzed: str, most_recent_module_commit_analyzed: str
    ) -> None:
        """
        Update most recent commit fields on an instance of TaskConfig.

        :param most_recent_project_commit_analyzed: The most recent project commit analyzed of the project.
        :param most_recent_module_commit_analyzed: Most_recent_module_commit_analyzed of the config.
        """
        self.most_recent_project_commit_analyzed = most_recent_project_commit_analyzed
        self.most_recent_module_commit_analyzed = most_recent_module_commit_analyzed

    def as_dict(self) -> Dict[str, Optional[str]]:
        """Return fields to be stored in database."""
        return {
            "most_recent_project_commit_analyzed": self.most_recent_project_commit_analyzed,
            "source_file_regex": self.source_file_regex,
            "test_file_regex": self.test_file_regex,
            "module": self.module,
            "most_recent_module_commit_analyzed": self.most_recent_module_commit_analyzed,
            "module_source_file_regex": self.module_source_file_regex,
            "module_test_file_regex": self.module_test_file_regex,
        }


class ProjectConfig:
    """Represents a project config for an Evergreen project."""

    def __init__(self, project: str, task_config: TaskConfig, test_config: TestConfig):
        """Init a ProjectConfig instance. Use ProjectConfig.get rather than this directly."""
        self.project = project
        self.task_config = task_config
        self.test_config = test_config

    @classmethod
    def get(cls, collection: Collection, project: str) -> ProjectConfig:
        """
        Fetch a project config from the db. If it doesn't exist, create an empty ProjectConfig.

        :param collection: The collection containing project config documents.
        :param project: The project being fetched.
        :return: An instance of ProjectConfig.
        """
        data = collection.find_one({"project": project})
        if data:
            return cls(
                project,
                TaskConfig.from_json(data.get("task_config")),
                TestConfig.from_json(data.get("test_config")),
            )
        return cls(project, TaskConfig(), TestConfig())

    def save(self, collection: Collection) -> None:
        """
        Save a ProjectConfig instance to the db collection.

        :param collection: The collection containing project config documents.
        """
        collection.update(
            {"project": self.project},
            {
                "$set": {
                    "task_config": self.task_config.as_dict(),
                    "test_config": self.test_config.as_dict(),
                }
            },
            upsert=True,
        )
