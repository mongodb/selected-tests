"""Method to create the task mappings for a given evergreen project."""
from concurrent.futures import ThreadPoolExecutor as Executor
from datetime import datetime
from typing import List, Dict, Set
from tempfile import TemporaryDirectory
from re import match
from typing import Pattern

from evergreen.api import Version, Build, Task, EvergreenApi
from evergreen.manifest import ManifestModule
from boltons.iterutils import windowed_iter
from git import Repo, DiffIndex
from structlog import get_logger

from selectedtests.git_helper import get_changed_files, init_repo
from selectedtests.evergreen_helper import get_evg_project

LOGGER = get_logger(__name__)

MAX_WORKERS = 32
SEEN_COUNT_KEY = "seen_count"
TASK_BUILDS_KEY = "builds"


class TaskMappings:
    """Represents and creates the task mappings for an evergreen project."""

    def __init__(self, mappings: Dict, evergreen_project: str, repo_name: str, branch: str):
        """Init a taskmapping instance. Use create_task_mappings rather than this directly."""
        self.mappings = mappings
        self.evergreen_project = evergreen_project
        self.repo_name = repo_name
        self.branch = branch

    @classmethod
    def create_task_mappings(
        cls,
        evg_api: EvergreenApi,
        evergreen_project: str,
        after_date: datetime,
        before_date: datetime,
        file_regex: Pattern,
        module_name: str = None,
        module_file_regex: Pattern = None,
        build_regex: Pattern = None,
    ):
        """
        Create the task mappings for an evergreen project. Optionally looks at an associated module.

        :param evg_api: An instance of the evg_api client
        :param evergreen_project: The name of the evergreen project to analyze.
        :param after_date: The date at which to start analyzing versions of the project.
        :param before_date: The date up to which we should analyze versions of the project.
        :param file_regex: Regex pattern to match changed files against.
        :param module_name: Name of the module associated with the evergreen project to also analyze
        :param module_file_regex: Regex pattern to match changed files of the module against.
        :param build_regex: Regex pattern to match build variant names against. Defaults to None.
        :return: An instance of the task mappings class
        """
        log = LOGGER.bind(
            project=evergreen_project,
            module=module_name,
            after_date=after_date,
            before_date=before_date,
        )
        log.info("Starting to generate task mappings")
        project_versions = evg_api.versions_by_project_time_window(
            evergreen_project, before_date, after_date
        )

        task_mappings = {}

        module_repo: Repo = None
        branch = None
        repo_name = None

        with TemporaryDirectory() as temp_dir:
            try:
                base_repo = _get_evg_project_and_init_repo(evg_api, evergreen_project, temp_dir)
            except ValueError:
                LOGGER.warning("Unexpected exception", exc_info=True)
                raise

            jobs = []
            with Executor(max_workers=MAX_WORKERS) as exe:
                for next_version, version, prev_version in windowed_iter(project_versions, 3):
                    if not branch or not repo_name:
                        branch = version.branch
                        repo_name = version.repo

                    LOGGER.info(f"Processing mappings for version", version=version.version_id)

                    try:
                        diff = _get_diff(base_repo, version.revision, prev_version.revision)
                    except ValueError:
                        LOGGER.warning("Unexpected exception", exc_info=True)
                        continue

                    changed_files = _get_filtered_files(diff, file_regex)

                    if module_name:
                        cur_module = _get_associated_module(version, module_name)
                        prev_module = _get_associated_module(prev_version, module_name)
                        if cur_module is not None and module_repo is None:
                            module_repo = init_repo(
                                temp_dir, cur_module.repo, cur_module.branch, cur_module.owner
                            )

                        module_changed_files = _get_module_changed_files(
                            module_repo, cur_module, prev_module, module_file_regex
                        )
                        changed_files = changed_files.union(module_changed_files)

                    jobs.append(
                        exe.submit(
                            _process_evg_version,
                            prev_version,
                            version,
                            next_version,
                            build_regex,
                            changed_files,
                        )
                    )

            for job in jobs:
                changed_files, flipped_tasks = job.result()
                if len(flipped_tasks) > 0:
                    _map_tasks_to_files(changed_files, flipped_tasks, task_mappings)

        return TaskMappings(task_mappings, evergreen_project, repo_name, branch)

    def transform(self) -> List[Dict]:
        """
        Transform the task mappings into how it will get stored in the database.

        :return: An array of dictionaries. Becomes an array of changed files that have in them the
         builds and the tasks in those that changed when that file did.
        """
        task_mappings = []
        for mapping in self.mappings:
            cur_mappings = self.mappings.get(mapping)
            new_mapping = {
                "source_file": mapping,
                "project": self.evergreen_project,
                "repo": self.repo_name,
                "branch": self.branch,
                "source_file_seen_count": cur_mappings.get(SEEN_COUNT_KEY),
            }
            new_tasks = []
            builds = cur_mappings.get(TASK_BUILDS_KEY)
            for build in builds:
                tasks = builds.get(build)
                for task in tasks:
                    new_tasks.append(
                        {"name": task, "variant": build, "flip_count": tasks.get(task)}
                    )
            new_mapping["tasks"] = new_tasks
            task_mappings.append(new_mapping)
        LOGGER.info("Generated task mappings list", task_mappings_length=len(task_mappings))
        return task_mappings


def _get_evg_project_and_init_repo(
    evg_api: EvergreenApi, evergreen_project: str, temp_dir: TemporaryDirectory
):
    project_info = get_evg_project(evg_api, evergreen_project)
    if project_info is None:
        raise ValueError(f"The evergreen project {evergreen_project} does not exist")
    return init_repo(
        temp_dir, project_info.repo_name, project_info.branch_name, project_info.owner_name
    )


def _get_filtered_files(diff: DiffIndex, regex: Pattern) -> Set[str]:
    """
    Get the list of changed files.

    :param diff: The diff between two commits.
    :param regex: The regex pattern to match the files found in the diff against.
    :return: A list of the changed files that matched the given regex pattern.
    """
    return {file for file in get_changed_files(diff, LOGGER) if match(regex, file)}


def _get_module_changed_files(
    module_repo: Repo,
    cur_module: ManifestModule,
    prev_module: ManifestModule,
    module_file_regex: Pattern,
) -> Set[str]:
    """
    Get the files that changed in the associated module.

    :param module_repo: The repo that contains the source code for the associated module.
    :param cur_module: The module version associated with the version being analyzed.
    :param prev_module: The module associated with the parent of the current version.
    :param module_file_regex: Regex pattern to match any files found in the diff against.
    :return: Set of changed files from the diff between the two module versions
     that match the given pattern.
    """
    if cur_module is None or prev_module is None:
        return set()

    if cur_module.revision != prev_module.revision:
        try:
            module_diff = _get_diff(module_repo, cur_module.revision, prev_module.revision)
        except ValueError:
            LOGGER.warning("Unexpected exception", exc_info=True)
            return set()
        return _get_filtered_files(module_diff, module_file_regex)

    return set()


def _get_associated_module(version: Version, module_name: str) -> ManifestModule:
    """
    Get the associated module for the given version.

    :param version: The version to get the module from.
    :param module_name: The name of the module to get.
    :return: The module that was asked for. Can return None if that module wasn't found.
    """
    modules = version.get_manifest().modules
    return modules.get(module_name)


def _get_diff(repo: Repo, cur_revision: str, prev_revision: str) -> DiffIndex:
    """
    Create a diff between two revisions.

    :param repo: The repo that contains the two given revisions.
    :param cur_revision: The child revision.
    :param prev_revision: The parent revision.
    :return: The diff between the two given revisions.
    """
    cur_commit = repo.commit(cur_revision)
    parent = repo.commit(prev_revision)

    return cur_commit.diff(parent)


def _map_tasks_to_files(changed_files: List[str], flipped_tasks: Dict, task_mappings: Dict):
    """
    Map the flipped tasks to the changed files found in this version. Mapping will be done in \
    place in the dictionary given in the task_mappings parameter.

    :param changed_files: List of the files that changed in this version.
    :param flipped_tasks: Dictionary that contains the build variants as keys and the list of tasks
     that changed in that variant as the value.
    :param task_mappings: Where the mappings will be stored. New mappings will be added to this
     dictionary in place.
    """
    for file_name in changed_files:
        task_mappings_for_file = task_mappings.setdefault(
            file_name, {TASK_BUILDS_KEY: {}, SEEN_COUNT_KEY: 0}
        )
        task_mappings_for_file[SEEN_COUNT_KEY] = task_mappings_for_file[SEEN_COUNT_KEY] + 1
        build_mappings = task_mappings_for_file[TASK_BUILDS_KEY]
        for build_name in flipped_tasks:
            builds_to_task_mappings: Dict[str:Dict] = build_mappings.setdefault(build_name, {})
            for cur_task in flipped_tasks.get(build_name):
                cur_flips_for_task = builds_to_task_mappings.setdefault(cur_task, 0)
                builds_to_task_mappings[cur_task] = cur_flips_for_task + 1


def _filter_non_matching_distros(builds: List[Build], build_regex: Pattern) -> List[Build]:
    """
    Filter the distros that don't match the given regex.

    :param builds: The builds to put through the filter.
    :param build_regex: Regex to match the builds' display_names against
    :return: A list of the builds that are required.
    """
    if not build_regex:
        return builds
    return [build for build in builds if match(build_regex, build.display_name)]


def _process_evg_version(
    prev_version: Version,
    version: Version,
    next_version: Version,
    build_regex: Pattern,
    changed_files: Set[str],
) -> (Set[str], Dict):
    """
    Find flipped tasks for this evergreen version.

    Return the tasks along with the files that were changed in the evergreen version.

    :param prev_version: Previous evergreen version.
    :param version: Evergreen version to analyze.
    :param next_version: Next evergreen version.
    :param build_regex: Regex of builds to look at.
    :param changed_files: Set of files that have changed.
    :return: Tuple with changed files and flipped tasks.
    """
    flipped_tasks = _get_flipped_tasks(prev_version, version, next_version, build_regex)
    return changed_files, flipped_tasks


def _get_flipped_tasks(
    prev_version: Version, version: Version, next_version: Version, build_regex: Pattern
) -> Dict:
    """
    Get the tasks that flipped in the current version.

    :param prev_version: The parent of the current version.
    :param version: The version that is being analyzed.
    :param next_version: The child of the current version.
    :param build_regex: Regex to match the builds' display_names against
    :return: A dictionary with build variants as keys and the list of tasks that flipped in those
     variants as the values.
    """
    builds = version.get_builds()
    builds = _filter_non_matching_distros(builds, build_regex)
    flipped_tasks = {}
    for build in builds:
        flipped_tasks_in_build = _get_flipped_tasks_per_build(build, prev_version, next_version)
        if len(flipped_tasks_in_build) > 0:
            flipped_tasks[build.build_variant] = flipped_tasks_in_build
    return flipped_tasks


def _get_flipped_tasks_per_build(
    build: Build, prev_version: Version, next_version: Version
) -> List[Task]:
    """
    Get the flipped tasks in the given build.

    :param build: The build to analyze.
    :param prev_version: The parent version of the version the given build belongs to.
    :param next_version: The child version of the version the given build belongs to.
    :return: A list of all the flipped tasks that happened in the given build.
    """
    prev_build: Build = prev_version.build_by_variant(build.build_variant)
    next_build: Build = next_version.build_by_variant(build.build_variant)

    prev_tasks = _create_task_map(prev_build.get_tasks())
    next_tasks = _create_task_map(next_build.get_tasks())

    tasks = build.get_tasks()

    return [task.display_name for task in tasks if _is_task_a_flip(task, prev_tasks, next_tasks)]


def _create_task_map(tasks: [Task]) -> Dict:
    """
    Create a dictionary of tasks by display_name.

    :param tasks: List of tasks to map.
    :return: Dictionary of tasks by display_name.
    """
    return {task.display_name: task for task in tasks}


def _is_task_a_flip(task: Task, prev_tasks: Dict, next_tasks: Dict) -> bool:
    """
    Determine if given task has flipped to states in this version.

    :param task: Task to check.
    :param next_tasks: Dictionary of tasks in next version.
    :param prev_tasks: Dictionary of tasks in previous version.
    :return: True if task has flipped in this version.
    """
    if not task.activated:
        return False

    if not _check_meaningful_task_status(task):
        return False

    next_task: Task = next_tasks.get(task.display_name)
    if not next_task or not next_task.activated or not _check_meaningful_task_status(next_task):
        return False
    prev_task: Task = prev_tasks.get(task.display_name)
    if not prev_task or not prev_task.activated or not _check_meaningful_task_status(prev_task):
        return False

    if task.status == next_task.status and task.status != prev_task.status:
        return True

    return False


def _check_meaningful_task_status(task: Task) -> bool:
    """
    Check whether the script can make a meaningful judgement off the status of the given task.

    :param task: The task to analyze
    :return: A bool representing whether the task should be analyzed or not
    """
    return task.status.lower() == "success" or task.status.lower() == "failed"
