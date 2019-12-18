"""Domain object representing project config."""
from pymongo.collection import Collection


class TaskConfig:
    """Represents the task mappings config for a project config."""

    def __init__(
        self,
        most_recent_version_analyzed=None,
        source_file_regex=None,
        build_variant_regex=None,
        module=None,
        module_source_file_regex=None,
    ):
        """Init a TaskConfig instance. Use ProjectConfig.get rather than this directly."""
        self.most_recent_version_analyzed = most_recent_version_analyzed
        self.source_file_regex = source_file_regex
        self.build_variant_regex = build_variant_regex
        self.module = module
        self.module_source_file_regex = module_source_file_regex

    @classmethod
    def from_json(cls, json):
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
        most_recent_version_analyzed,
        source_file_regex,
        build_variant_regex,
        module,
        module_source_file_regex,
    ):
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

    def update_most_recent_version_analyzed(self, most_recent_version_analyzed):
        """
        Update most_recent_version_analyzed field on an instance of TaskConfig.

        :param most_recent_version_analyzed: The most recent version analyzed of the project.
        """
        self.most_recent_version_analyzed = most_recent_version_analyzed


class TestConfig:
    """Represents the test mappings config for a project config."""

    def __init__(
        self,
        most_recent_project_commit_analyzed=None,
        source_file_regex=None,
        test_file_regex=None,
        module=None,
        most_recent_module_commit_analyzed=None,
        module_source_file_regex=None,
        module_test_file_regex=None,
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
    def from_json(cls, json):
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
        most_recent_project_commit_analyzed,
        source_file_regex,
        test_file_regex,
        module,
        most_recent_module_commit_analyzed,
        module_source_file_regex,
        module_test_file_regex,
    ):
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
        self, most_recent_project_commit_analyzed, most_recent_module_commit_analyzed
    ):
        """
        Update most recent commit fields on an instance of TaskConfig.

        :param most_recent_version_analyzed: The most recent version analyzed of the project.
        :param most_recent_module_commit_analyzed: Most_recent_module_commit_analyzed of the config.
        """
        self.most_recent_project_commit_analyzed = most_recent_project_commit_analyzed
        self.most_recent_module_commit_analyzed = most_recent_module_commit_analyzed


class ProjectConfig:
    """Represents a project config for an Evergreen project."""

    def __init__(self, project, task_config: TaskConfig, test_config: TestConfig):
        """Init a ProjectConfig instance. Use ProjectConfig.get rather than this directly."""
        self.project = project
        self.task_config = task_config
        self.test_config = test_config

    @classmethod
    def get(cls, collection: Collection, project):
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

    def save(self, collection):
        """
        Save a ProjectConfig instance to the db collection.

        :param collection: The collection containing project config documents.
        """
        task_config = {
            "most_recent_version_analyzed": self.task_config.most_recent_version_analyzed,
            "source_file_regex": self.task_config.source_file_regex,
            "build_variant_regex": self.task_config.build_variant_regex,
            "module": self.task_config.module,
            "module_source_file_regex": self.task_config.module_source_file_regex,
        }
        most_recent_project_commit_analyzed = self.test_config.most_recent_project_commit_analyzed
        most_recent_module_commit_analyzed = self.test_config.most_recent_module_commit_analyzed
        test_config = {
            "most_recent_project_commit_analyzed": most_recent_project_commit_analyzed,
            "source_file_regex": self.test_config.source_file_regex,
            "test_file_regex": self.test_config.test_file_regex,
            "module": self.test_config.module,
            "most_recent_module_commit_analyzed": most_recent_module_commit_analyzed,
            "module_source_file_regex": self.test_config.module_source_file_regex,
            "module_test_file_regex": self.test_config.module_test_file_regex,
        }
        collection.update(
            {"project": self.project},
            {"$set": {"task_config": task_config, "test_config": test_config}},
            upsert=True,
        )
