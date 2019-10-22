"""Test Mappings class to create test mappings."""
import structlog
import os.path

from datetime import datetime
from collections import defaultdict
from structlog.stdlib import LoggerFactory
from selectedtests.git_helper import modified_files_for_commit
from re import Pattern
from git import Repo

structlog.configure(logger_factory=LoggerFactory())
LOGGER = structlog.get_logger(__name__)


class TestMappings(object):
    """Represents and creates the test mappings for an evergreen project."""

    def __init__(
        self,
        file_intersection: defaultdict,
        file_count_map: defaultdict,
        project: str,
        repo_name: str,
        branch: str,
    ):
        """
        Create a TestMappings object.

        :param file_intersection: Map of how files intersect.
        :param file_count_map: Map of how many times files where seen.
        """
        self._file_intersection = file_intersection
        self._file_count_map = file_count_map
        self._project = project
        self._repo_name = repo_name
        self._branch = branch
        self._test_mappings = None

    @classmethod
    def create_mappings(
        cls,
        repo: Repo,
        source_re: Pattern,
        test_re: Pattern,
        start_date: datetime,
        end_date: datetime,
        project: str,
        branch: str,
    ):
        """
        Create the test mappings for an evergreen project. Optionally looks at an associated module.

        :param repo: The repo that contains the source code for the evergreen project.
        :param source_re: Regex pattern to match changed source files against.
        :param test_re: Regex pattern to match changed test files against.
        :param start_date: The date at which to start analyzing commits of the project.
        :param end_date: The date up to which we should analyze commits of the project.
        :param project: The name of the evergreen project to analyze.
        :param branch: The branch of the git repo used for the evergreen project.
        :return: An instance of the test mappings class
        """
        file_intersection = defaultdict(lambda: defaultdict(int))
        file_count = defaultdict(int)

        LOGGER.debug("searching from", ts=start_date)
        LOGGER.debug("searching until", ts=end_date)
        for commit in repo.iter_commits(repo.head.commit):
            LOGGER.debug(
                "Investigating commit",
                summary=commit.message.splitlines()[0],
                ts=commit.committed_datetime,
                id=commit.hexsha,
            )

            if commit.committed_datetime.timestamp() < start_date.timestamp():
                break

            if commit.committed_datetime.timestamp() > end_date.timestamp():
                continue

            tests_changed = set()
            src_changed = set()
            for path in modified_files_for_commit(commit, LOGGER):
                LOGGER.debug("found change", path=path)

                if test_re.match(path):
                    tests_changed.add(path)
                elif source_re.match(path):
                    src_changed.add(path)

            for src in src_changed:
                file_count[src] += 1
                for test in tests_changed:
                    file_intersection[src][test] += 1

        repo_name = os.path.basename(repo.working_dir)
        return TestMappings(file_intersection, file_count, project, repo_name, branch)

    def get_mappings(self):
        """
        Get a transformed version of test mappings to the test mapping object.

        :return: Transformed test mappings
        """
        if not self._test_mappings:
            self._test_mappings = self._transform_mappings()
        return self._test_mappings

    def _transform_mappings(self):
        test_mappings = []
        for source_file, test_file_count_dict in self._file_intersection.items():
            test_files = []
            for test_file, test_file_seen_count in test_file_count_dict.items():
                test_files.append({"name": test_file, "test_file_seen_count": test_file_seen_count})
            test_mapping = {
                "source_file": source_file,
                "project": self._project,
                "repo": self._repo_name,
                "branch": self._branch,
                "source_file_seen_count": self._file_count_map[source_file],
                "test_files": test_files,
            }
            test_mappings.append(test_mapping)
        return test_mappings
