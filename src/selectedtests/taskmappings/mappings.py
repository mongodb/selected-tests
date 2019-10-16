from datetime import datetime
from typing import List, Dict, Generator
import os.path
import tempfile
from re import Pattern, match

from evergreen.api import Version, Build, Task, CachedEvergreenApi
from evergreen.manifest import ManifestModule
from boltons.iterutils import windowed_iter
from git import Repo, DiffIndex
from structlog import get_logger

LOGGER = get_logger(__name__)

GITHUB_BASE_URL = "https://github.com"
SEEN_COUNT_KEY = "seen_count"
TASK_BUILDS_KEY = "builds"


class TaskMappings:
    def __init__(self, mappings: Dict, evergreen_project: str, repo_name: str, branch: str):
        self.mappings = mappings
        self.evergreen_project = evergreen_project
        self.repo_name = repo_name
        self.branch = branch

    @classmethod
    def create_task_mappings(
        cls,
        evg_api: CachedEvergreenApi,
        evergreen_project: str,
        start_date: datetime,
        end_date: datetime,
        org_name: str,
        file_regex: Pattern,
        module_name: str,
        module_file_regex: Pattern,
    ):
        project_versions: Generator[Version] = evg_api.versions_by_project(evergreen_project)

        task_mappings = {}

        base_repo: Repo = None
        module_repo: Repo = None
        branch = ""
        repo_name = ""

        with tempfile.TemporaryDirectory() as temp_dir:
            for next_version, version, prev_version in windowed_iter(project_versions, 3):
                if version.create_time < start_date:
                    break
                if version.create_time > end_date:
                    continue
                if base_repo is None:
                    base_repo = _init_repo(temp_dir, org_name, version.repo, version.branch)

                LOGGER.info(f"Processing mappings for version {version.version_id}")

                branch = version.branch
                repo_name = version.repo
                try:
                    diff = _get_diff(base_repo, version.revision, prev_version.revision)
                except ValueError as e:
                    print(e)
                    continue

                changed_files = _get_filtered_files(diff, file_regex)

                cur_module = _get_associated_module(version, module_name)
                prev_module = _get_associated_module(prev_version, module_name)
                if cur_module is not None and module_repo is None:
                    module_repo = _init_repo(
                        temp_dir, cur_module.owner, cur_module.repo, cur_module.branch
                    )

                module_changed_files = _get_module_changed_files(
                    module_repo, cur_module, prev_module, module_file_regex
                )
                changed_files.extend(module_changed_files)

                flipped_tasks = _get_flipped_tasks(prev_version, version, next_version)

                if len(flipped_tasks) > 0:
                    _map_tasks_to_files(changed_files, flipped_tasks, task_mappings)

        return TaskMappings(task_mappings, evergreen_project, repo_name, branch)

    def transform(self) -> List[Dict]:
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
        return task_mappings


def _get_filtered_files(diff: DiffIndex, regex: Pattern) -> List[str]:
    re: List[str] = []
    for file in _get_changed_files(diff):
        if match(regex, file.b_path):
            re.append(file.b_path)
    return re


def _get_module_changed_files(
    module_repo: Repo,
    cur_module: ManifestModule,
    prev_module: ManifestModule,
    module_file_regex: Pattern,
) -> List[str]:
    if cur_module is None or prev_module is None:
        return []
    if cur_module.revision != prev_module.revision:
        try:
            module_diff = _get_diff(module_repo, cur_module.revision, prev_module.revision)
        except ValueError as e:
            LOGGER.error(str(e))
            return []
        return _get_filtered_files(module_diff, module_file_regex)
    return []


def _get_associated_module(version: Version, module_name: str) -> ManifestModule:
    modules = version.get_manifest().modules
    return modules.get(module_name)


def _get_diff(repo: Repo, cur_revision: str, prev_revision: str) -> DiffIndex:
    cur_commit = repo.commit(cur_revision)
    parent = repo.commit(prev_revision)

    return cur_commit.diff(parent)


def _map_tasks_to_files(changed_files: List[str], flipped_tasks: Dict, task_mappings: Dict):
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


def _init_repo(temp_dir, org_name: str, repo_name: str, branch: str) -> Repo:
    repo_path = os.path.join(temp_dir, repo_name)
    if os.path.exists(repo_path):
        repo = Repo(repo_path)
        repo.remotes["origin"].pull()
    else:
        url = f"{GITHUB_BASE_URL}/{org_name}/{repo_name}.git"
        repo = Repo.clone_from(url, repo_path)
    origin = repo.remotes["origin"]
    repo.create_head(branch, origin.refs[branch]).set_tracking_branch(
        origin.refs[branch]
    ).checkout()
    return repo


def _get_changed_files(diff: DiffIndex):
    for patch in diff.iter_change_type("M"):
        yield patch

    for patch in diff.iter_change_type("A"):
        yield patch

    for patch in diff.iter_change_type("R"):
        yield patch


def _filter_non_required_distros(builds: List[Build]) -> List[Build]:
    return [build for build in builds if build.display_name.startswith("!")]


def _get_flipped_tasks(prev_version: Version, version: Version, next_version: Version) -> Dict:
    builds = version.get_builds()
    builds = _filter_non_required_distros(builds)
    flipped_tasks = {}
    for build in builds:
        flipped_tasks_in_build = _get_flipped_tasks_per_build(build, prev_version, next_version)
        if len(flipped_tasks_in_build) > 0:
            flipped_tasks[build.build_variant] = flipped_tasks_in_build
    return flipped_tasks


def _get_flipped_tasks_per_build(
    build: Build, prev_version: Version, next_version: Version
) -> List[Task]:
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

    if task.status.lower() != "success" and task.status.lower() != "failed":
        return False

    next_task: Task = next_tasks.get(task.display_name)
    if not next_task or not next_task.activated:
        return False
    prev_task: Task = prev_tasks.get(task.display_name)
    if not prev_task or not prev_task.activated:
        return False

    if task.status == next_task.status and task.status != prev_task.status:
        return True

    return False
