"""Test Mappings class to create test mappings."""
import os.path
import re
import structlog

from tempfile import TemporaryDirectory
from typing import Pattern, Tuple
from collections import defaultdict, namedtuple
from evergreen.api import EvergreenApi
from git import Repo

from selectedtests.evergreen_helper import get_evg_project, get_evg_module_for_project
from selectedtests.git_helper import init_repo, modified_files_for_commit
from selectedtests.test_mappings.commit_limit import CommitLimit

LOGGER = structlog.get_logger(__name__)
TestMappingsResult = namedtuple(
    "TestMappingsResult",
    [
        "test_mappings_list",
        "most_recent_project_commit_analyzed",
        "most_recent_module_commit_analyzed",
    ],
)


def generate_test_mappings(
    evg_api: EvergreenApi,
    evergreen_project: str,
    project_commit_limit: CommitLimit,
    source_file_regex: str,
    test_file_regex: str,
    module_name: str = None,
    module_commit_limit: CommitLimit = None,
    module_source_file_regex: str = None,
    module_test_file_regex: str = None,
) -> TestMappingsResult:
    """
    Generate test mappings for an evergreen project and its associated module if module is provided.

    :param evg_api: An instance of the evg_api client.
    :param evergreen_project: The name of the evergreen project to analyze.
    :param project_commit_limit: The point in time at which to start analyzing project commits.
    :param source_file_regex: Regex pattern to match changed source files against.
    :param test_file_regex: Regex pattern to match changed test files against.
    :param module_name: The name of the module to analyze.
    :param module_commit_limit: The point in time at which to start analyzing commits of the module.
    :param module_source_file_regex: Regex pattern to match changed module source files against.
    :param module_test_file_regex: Regex pattern to match changed module test files against.
    :return: An instance of TestMappingsResult.
    """
    log = LOGGER.bind(
        project=evergreen_project,
        module=module_name,
        project_commit_limit_stop_at_date=project_commit_limit.stop_at_date,
        project_commit_limit_stop_at_commit_sha=project_commit_limit.stop_at_commit_sha,
    )
    log.info("Starting to generate test mappings")

    source_re = re.compile(source_file_regex)
    test_re = re.compile(test_file_regex)
    module_source_re = None
    module_test_re = None
    if module_name:
        module_source_re = re.compile(module_source_file_regex)
        module_test_re = re.compile(module_test_file_regex)

    most_recent_module_commit = None
    with TemporaryDirectory() as temp_dir:
        test_mappings_list, most_recent_project_commit = generate_project_test_mappings(
            evg_api, evergreen_project, temp_dir, source_re, test_re, project_commit_limit
        )

        if module_name:
            module_test_mappings_list, most_recent_module_commit = generate_module_test_mappings(
                evg_api,
                evergreen_project,
                module_name,
                temp_dir,
                module_source_re,
                module_test_re,
                module_commit_limit,
            )
            test_mappings_list.extend(module_test_mappings_list)
    log.info("Generated test mappings list", test_mappings_length=len(test_mappings_list))
    return TestMappingsResult(
        test_mappings_list=test_mappings_list,
        most_recent_project_commit_analyzed=most_recent_project_commit,
        most_recent_module_commit_analyzed=most_recent_module_commit,
    )


def generate_project_test_mappings(
    evg_api: EvergreenApi,
    evergreen_project: str,
    temp_dir: TemporaryDirectory,
    source_re: Pattern,
    test_re: Pattern,
    commit_limit: CommitLimit,
) -> Tuple[list, str]:
    """
    Generate test mappings for an evergreen project.

    :param evg_api: An instance of the evg_api client
    :param evergreen_project: The name of the evergreen project to analyze.
    :param temp_dir: The place where to clone the repo to.
    :param source_re: Regex pattern to match changed source files against.
    :param test_re: Regex pattern to match changed test files against.
    :param commit_limit: The point in time at which to start analyzing project commits's repo.
    :return: A list of test mappings for the project and the most recent commit sha analyzed.
    """
    evg_project = get_evg_project(evg_api, evergreen_project)
    project_repo = init_repo(
        temp_dir, evg_project.repo_name, evg_project.branch_name, evg_project.owner_name
    )
    most_recent_project_commit_analyzed = project_repo.head.commit.hexsha
    LOGGER.info(
        "Calculated most_recent_project_commit_analyzed",
        most_recent_project_commit_analyzed=most_recent_project_commit_analyzed,
    )
    project_test_mappings = TestMappings.create_mappings(
        project_repo, source_re, test_re, commit_limit, evergreen_project, evg_project.branch_name
    )
    return project_test_mappings.get_mappings(), most_recent_project_commit_analyzed


def generate_module_test_mappings(
    evg_api: EvergreenApi,
    evergreen_project: str,
    module_name: str,
    temp_dir: TemporaryDirectory,
    module_source_re: Pattern,
    module_test_re: Pattern,
    commit_limit: CommitLimit,
) -> Tuple[list, str]:
    """
    Generate test mappings for an evergreen module.

    :param evg_api: An instance of the evg_api client
    :param evergreen_project: The name of the evergreen project that the module belongs to.
    :param module_name: The name of the module to analyze.
    :param temp_dir: The place where to clone the repo to.
    :param module_source_re: Regex pattern to match changed module source files against.
    :param module_test_re: Regex pattern to match changed module test files against.
    :param commit_limit: The point in time at which to start analyzing commits of the module's repo.
    :return: A list of test mappings for the project and the most recent commit sha analyzed.
    """
    module = get_evg_module_for_project(evg_api, evergreen_project, module_name)
    module_repo = init_repo(temp_dir, module.repo, module.branch, module.owner)
    most_recent_module_commit_analyzed = module_repo.head.commit.hexsha
    LOGGER.info(
        "Calculated most_recent_module_commit_analyzed",
        most_recent_module_commit_analyzed=most_recent_module_commit_analyzed,
    )
    module_test_mappings = TestMappings.create_mappings(
        module_repo,
        module_source_re,
        module_test_re,
        commit_limit,
        evergreen_project,
        module.branch,
    )
    return module_test_mappings.get_mappings(), most_recent_module_commit_analyzed


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
        :param project: The name of the evergreen project to analyze.
        :param repo_name: The name of the git repo used for the evergreen project.
        :param branch: The branch of the git repo used for the evergreen project.
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
        commit_limit: CommitLimit,
        project: str,
        branch: str,
    ):
        """
        Create the test mappings for a git repo.

        :param repo: The repo that contains the source code for the evergreen project.
        :param source_re: Regex pattern to match changed source files against.
        :param test_re: Regex pattern to match changed test files against.
        :param commit_limit: The point in time at which to start analyzing commits of the repo.
        :param project: The name of the evergreen project to analyze.
        :param branch: The branch of the git repo used for the evergreen project.
        :return: An instance of the test mappings class
        """
        file_intersection = defaultdict(lambda: defaultdict(int))
        file_count = defaultdict(int)

        for commit in repo.iter_commits(repo.head.commit):
            if commit_limit.check_commit_before_limit(commit):
                break

            LOGGER.debug(
                "Investigating commit",
                summary=commit.message.splitlines()[0],
                ts=commit.committed_datetime,
                id=commit.hexsha,
            )

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
            test_files = [
                {"name": test_file, "test_file_seen_count": test_file_seen_count}
                for test_file, test_file_seen_count in test_file_count_dict.items()
            ]
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
