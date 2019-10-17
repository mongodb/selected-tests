from unittest.mock import MagicMock, patch
from datetime import datetime, date, time
import re
from copy import deepcopy

from selectedtests.task_mappings import mappings as under_test


NS = "selectedtests.task_mappings.mappings"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestCreateTaskMappings:
    @patch(ns("_init_repo"))
    @patch(ns("_get_diff"))
    @patch(ns("_get_filtered_files"))
    @patch(ns("_get_associated_module"))
    @patch(ns("_get_module_changed_files"))
    @patch(ns("_get_flipped_tasks"))
    def test_module_source_files_included(
        self,
        flipped_mock,
        module_changed_mock,
        associated_module_mock,
        filtered_mock,
        diff_mock,
        init_repo_mock,
    ):
        evg_api_mock = MagicMock()
        evg_api_mock.versions_by_project.return_value = [
            MagicMock(create_time=datetime.combine(date(1, 1, 1), time(1, 2, i))) for i in range(3)
        ]
        evg_api_mock.versions_by_project.return_value.reverse()
        associated_module_mock.return_value = None

        module_changed_mock.return_value = ["module_file"]
        filtered_mock.return_value = [f"file{i}" for i in range(2)]

        expected_file_list = deepcopy(module_changed_mock.return_value) + deepcopy(
            filtered_mock.return_value
        )

        flipped_mock.return_value = {"variant1": ["task1", "task2"], "variant2": ["task3", "task4"]}
        project_name = "project"

        start = datetime.combine(date(1, 1, 1), time(1, 1, 0))
        end = datetime.combine(date(1, 1, 1), time(1, 3, 0))

        mappings = under_test.TaskMappings.create_task_mappings(
            evg_api_mock, project_name, start, end, None, None, "module", None
        )

        assert len(expected_file_list) == len(mappings.mappings)
        for file in expected_file_list:
            file_mappings = mappings.mappings.get(file)["builds"]
            assert 1 == mappings.mappings.get(file)[under_test.SEEN_COUNT_KEY]
            assert file_mappings is not None
            for variant in flipped_mock.return_value:
                expected_tasks = flipped_mock.return_value.get(variant)
                variant_output = file_mappings.get(variant)
                assert variant_output is not None
                for task in expected_tasks:
                    assert task in variant_output

    @patch(ns("_init_repo"))
    @patch(ns("_get_diff"))
    @patch(ns("_get_filtered_files"))
    @patch(ns("_get_associated_module"))
    @patch(ns("_get_module_changed_files"))
    @patch(ns("_get_flipped_tasks"))
    def test_module_source_files_not_included_if_no_module_passed_in(
        self,
        flipped_mock,
        module_changed_mock,
        associated_module_mock,
        filtered_mock,
        diff_mock,
        init_repo_mock,
    ):
        evg_api_mock = MagicMock()
        evg_api_mock.versions_by_project.return_value = [
            MagicMock(create_time=datetime.combine(date(1, 1, 1), time(1, 2, i))) for i in range(3)
        ]
        evg_api_mock.versions_by_project.return_value.reverse()

        # We still mock the two below so that we can check to make sure even if the version has a
        # module and that module has changed files in it, we don't actually add the changed files
        # to the task mappings if they're not asked for
        module_changed_mock.return_value = ["module_file"]
        associated_module_mock.return_value = None

        filtered_mock.return_value = [f"file{i}" for i in range(2)]
        expected_file_list = deepcopy(filtered_mock.return_value)

        flipped_mock.return_value = {"variant1": ["task1", "task2"], "variant2": ["task3", "task4"]}
        project_name = "project"

        start = datetime.combine(date(1, 1, 1), time(1, 1, 0))
        end = datetime.combine(date(1, 1, 1), time(1, 3, 0))

        mappings = under_test.TaskMappings.create_task_mappings(
            evg_api_mock, project_name, start, end, None, None, "", None
        )

        assert len(expected_file_list) == len(mappings.mappings)
        # Here we're checking to make sure the files that were changed in the module aren't
        # added to the mappings
        for file in module_changed_mock.return_value:
            assert file not in mappings.mappings.keys()

        for file in expected_file_list:
            file_mappings = mappings.mappings.get(file)["builds"]
            assert 1 == mappings.mappings.get(file)[under_test.SEEN_COUNT_KEY]
            assert file_mappings is not None
            for variant in flipped_mock.return_value:
                expected_tasks = flipped_mock.return_value.get(variant)
                variant_output = file_mappings.get(variant)
                assert variant_output is not None
                for task in expected_tasks:
                    assert task in variant_output

    @patch(ns("_init_repo"))
    @patch(ns("_get_diff"))
    @patch(ns("_get_filtered_files"))
    @patch(ns("_get_flipped_tasks"))
    def test_no_flipped_tasks_creates_no_mappings(
        self, flipped_mock, filtered_mock, diff_mock, init_repo_mock
    ):
        evg_api_mock = MagicMock()
        evg_api_mock.versions_by_project.return_value = [
            MagicMock(create_time=datetime.combine(date(1, 1, 1), time(1, 2, i))) for i in range(3)
        ]
        evg_api_mock.versions_by_project.return_value.reverse()
        filtered_mock.return_value = [f"file{i}" for i in range(2)]

        flipped_mock.return_value = {}
        project_name = "project"

        start = datetime.combine(date(1, 1, 1), time(1, 1, 0))
        end = datetime.combine(date(1, 1, 1), time(1, 3, 0))

        mappings = under_test.TaskMappings.create_task_mappings(
            evg_api_mock, project_name, start, end, None, None, "", None
        )

        assert 0 == len(mappings.mappings)

    @patch(ns("_init_repo"))
    @patch(ns("_get_diff"))
    @patch(ns("_get_filtered_files"))
    @patch(ns("_get_flipped_tasks"))
    def test_only_versions_in_given_range_are_analyzed(
        self, flipped_mock, filtered_mock, diff_mock, init_repo_mock
    ):
        evg_api_mock = MagicMock()
        evg_api_mock.versions_by_project.return_value = [
            MagicMock(create_time=datetime.combine(date(1, 1, 1), time(i, 1, 0)), revision=i)
            for i in range(7)
        ]
        evg_api_mock.versions_by_project.return_value.reverse()

        # This time range will only analyze the version where i=3 in the versions made above
        desired_start = datetime.combine(date(1, 1, 1), time(2, 30, 0))
        desired_end = datetime.combine(date(1, 1, 1), time(3, 30, 0))

        # We check for revision=3 here as that's the only version that should be analyzed
        # in the given time range
        def get_diff(repo, cur_revision, prev_revision):
            if cur_revision == 3:
                return MagicMock(expected=True)
            return MagicMock(expected=False)

        diff_mock.side_effect = get_diff

        expected_files = [f"file{i}" for i in range(2)]
        bad_file_list = ["bad_file"]

        def get_filtered_files(diff, regex):
            if diff.expected:
                return expected_files
            return bad_file_list

        filtered_mock.side_effect = get_filtered_files

        flipped_mock.return_value = {"variant1": ["task1", "task2"], "variant2": ["task3", "task4"]}
        project_name = "project"

        mappings = under_test.TaskMappings.create_task_mappings(
            evg_api_mock, project_name, desired_start, desired_end, None, None, "", None
        )

        assert len(expected_files) == len(mappings.mappings)
        for file in bad_file_list:
            assert file not in mappings.mappings.keys()

        for file in expected_files:
            file_mappings = mappings.mappings.get(file)["builds"]
            assert 1 == mappings.mappings.get(file)[under_test.SEEN_COUNT_KEY]
            assert file_mappings is not None
            for variant in flipped_mock.return_value:
                expected_tasks = flipped_mock.return_value.get(variant)
                variant_output = file_mappings.get(variant)
                assert len(expected_tasks) == len(variant_output)
                assert variant_output is not None
                for task in expected_tasks:
                    assert task in variant_output


class TestTransformationOfTaskMappings:
    def test_basic_transformation(self):
        num_tasks = 2
        task_mappings = {}
        changed_files = [f"test{i}" for i in range(2)]
        flipped_tasks = {
            "build1": [f"task{i}" for i in range(num_tasks)],
            "build2": [f"task{i}" for i in range(num_tasks)],
        }

        under_test._map_tasks_to_files(changed_files, flipped_tasks, task_mappings)

        evergreen_project, repo_name, branch_name = "evergreen", "repo", "branch"

        task_mappings = under_test.TaskMappings(
            task_mappings, evergreen_project, repo_name, branch_name
        )

        transformed_mappings = task_mappings.transform()

        assert len(transformed_mappings) == len(changed_files)

        expected_transformed_tasks = []

        for build in flipped_tasks:
            tasks = flipped_tasks[build]
            for task in tasks:
                expected_transformed_tasks.append(
                    self._make_transformed_task_helper(task, build, 1)
                )

        for mapping in transformed_mappings:
            assert mapping.get("source_file") in changed_files
            assert mapping.get("project") == evergreen_project
            assert mapping.get("repo") == repo_name
            assert mapping.get("branch") == branch_name
            assert mapping.get("source_file_seen_count") == 1
            assert len(mapping.get("tasks")) == len(flipped_tasks) * num_tasks
            assert mapping.get("tasks") == expected_transformed_tasks

    def _make_transformed_task_helper(self, name: str, variant: str, flip_count: int):
        return {"name": name, "variant": variant, "flip_count": flip_count}


class TestFilteredFiles:
    @patch(ns("_get_changed_files"))
    def test_filter_files_by_regex(self, changed_files_mock):
        def changed_files(diff):
            letters = ["a", "b", "c", "ab", "ac", "ba", "bc", "ca", "cb", "abc/test"]
            return [MagicMock(b_path=l) for l in letters]

        changed_files_mock.side_effect = changed_files

        regex = re.compile("a.*")
        filtered = under_test._get_filtered_files(None, regex)

        expected = ["a", "ab", "ac", "abc/test"]

        assert len(filtered) == 4
        for letter in expected:
            assert letter in filtered


class TestMapTasksToFiles:
    def test_basic_mapping(self):
        task_mappings = {}
        changed_files = [f"test{i}" for i in range(5)]
        flipped_tasks = {
            "build1": [f"task{i}" for i in range(5)],
            "build2": [f"task{i}" for i in range(5)],
        }

        under_test._map_tasks_to_files(changed_files, flipped_tasks, task_mappings)

        for file in changed_files:
            file_mapping = task_mappings.get(file)
            assert file_mapping is not None
            assert file_mapping["seen_count"] == 1
            build_mappings = file_mapping.get("builds")
            assert build_mappings is not None
            for build in flipped_tasks:
                task_mapping_for_file = build_mappings.get(build)
                assert task_mapping_for_file is not None

                for task in flipped_tasks.get(build):
                    assert task in task_mapping_for_file

    def test_adding_to_existing_mapping(self):
        task_mappings = {}
        changed_files1 = [f"file{i}" for i in range(1)]

        small_task_list = [f"task{i}" for i in range(2)]
        large_task_list = [f"task{i}" for i in range(4)]

        flipped_tasks1 = {"build1": small_task_list, "build2": small_task_list}

        under_test._map_tasks_to_files(changed_files1, flipped_tasks1, task_mappings)

        expected_after_first = {
            "file0": {
                "builds": {"build1": {"task0": 1, "task1": 1}, "build2": {"task0": 1, "task1": 1}},
                "seen_count": 1,
            }
        }

        assert expected_after_first == task_mappings

        changed_files2 = [f"file{i}" for i in range(2)]
        flipped_tasks2 = {"build1": large_task_list, "build3": small_task_list}

        under_test._map_tasks_to_files(changed_files2, flipped_tasks2, task_mappings)

        untouched_large_task_dict = {"task0": 1, "task1": 1, "task2": 1, "task3": 1}
        expected_small_task_dict = {"task0": 1, "task1": 1}
        modified_large_task_dict = {"task0": 2, "task1": 2, "task2": 1, "task3": 1}
        expected_task_mappings = {
            "file0": {
                "seen_count": 2,
                "builds": {
                    "build1": modified_large_task_dict,
                    "build2": expected_small_task_dict,
                    "build3": expected_small_task_dict,
                },
            },
            "file1": {
                "seen_count": 1,
                "builds": {"build1": untouched_large_task_dict, "build3": expected_small_task_dict},
            },
        }

        assert expected_task_mappings == task_mappings


class TestFilterDistros:
    def test_filter_non_required_distros(self):
        required_distros = [MagicMock(display_name=f"!distro{i}") for i in range(5)]
        optional_distros = [MagicMock(display_name=f"distro{i}") for i in range(10)]

        fitered_distros = under_test._filter_non_required_distros(
            required_distros + optional_distros
        )

        assert len(required_distros) == len(fitered_distros)
        for distro in required_distros:
            assert distro in fitered_distros
        for distro in optional_distros:
            assert distro not in fitered_distros

    def test_filter_all_distros(self):
        optional_distros = [MagicMock(display_name=f"distro{i}") for i in range(10)]

        filtered_distros = under_test._filter_non_required_distros(optional_distros)

        assert 0 == len(filtered_distros)
        for distro in optional_distros:
            assert distro not in filtered_distros


class TestGetFlippedTasks:
    @patch(ns("_get_flipped_tasks_per_build"))
    def test_get_flipped_tasks(self, _get_flips_mock):
        prev_version_mock = MagicMock()
        version_mock = MagicMock()
        next_version_mock = MagicMock()

        expected_tasks = ["task1", "task2"]

        _get_flips_mock.return_value = expected_tasks

        required_distros = [
            MagicMock(display_name=f"!distro{i}", build_variant=f"distro{i}") for i in range(5)
        ]
        optional_distros = [
            MagicMock(display_name=f"distro{i}", build_variant=str(i % 2) == 0) for i in range(10)
        ]

        all_distros = []
        all_distros.extend(required_distros)
        all_distros.extend(optional_distros)

        version_mock.get_builds.return_value = all_distros

        flipped_tasks = under_test._get_flipped_tasks(
            prev_version_mock, version_mock, next_version_mock
        )

        assert len(required_distros) == len(flipped_tasks)

        for mock_distro in required_distros:
            tasks = flipped_tasks.get(mock_distro.build_variant)
            assert tasks is not None
            assert len(tasks) == len(expected_tasks)
            for task in expected_tasks:
                assert task in tasks


class TestFlippedTasksPerBuild:
    def test_get_flipped_tasks_per_build(self):
        build_variant = "test"
        tasks = [
            _mock_task(display_name=str(i), activated=True, status="Success") for i in range(12)
        ]
        build_mock = MagicMock(build_variant=build_variant)
        build_mock.get_tasks.return_value = tasks

        prev_version = MagicMock()
        prev_build = MagicMock()
        prev_build.get_tasks.return_value = [
            _mock_task(
                display_name=str(i), activated=True, status="Success" if (i % 2 == 0) else "Failed"
            )
            for i in range(11)
        ]
        prev_version.build_by_variant.return_value = prev_build

        next_version = MagicMock()
        next_build = MagicMock()
        next_build.get_tasks.return_value = [
            _mock_task(
                display_name=str(i), activated=True, status="Success" if (i % 3 == 0) else "Failed"
            )
            for i in range(11)
        ]
        next_version.build_by_variant.return_value = next_build

        flipped_tasks = under_test._get_flipped_tasks_per_build(
            build_mock, prev_version, next_version
        )

        expected = ["3", "9"]

        assert len(flipped_tasks) == len(expected)

        for name in expected:
            assert name in flipped_tasks

    def test_no_get_flipped_tasks_if_tasks_werent_active(self):
        build_variant = "test"
        tasks = [_mock_task(display_name=str(i), activated=False, status="True") for i in range(10)]
        build_mock = MagicMock(build_variant=build_variant)
        build_mock.get_tasks.return_value = tasks

        prev_version = MagicMock()
        prev_build = MagicMock()
        prev_build.get_tasks.return_value = [
            _mock_task(display_name=str(i), status=str(i % 2 == 0)) for i in range(9)
        ]
        prev_version.build_by_variant.return_value = prev_build

        next_version = MagicMock()
        next_build = MagicMock()
        next_build.get_tasks.return_value = [
            _mock_task(display_name=str(i), status=str(i % 3 == 0)) for i in range(9)
        ]
        next_version.build_by_variant.return_value = next_build

        flipped_tasks = under_test._get_flipped_tasks_per_build(
            build_mock, prev_version, next_version
        )

        assert len(flipped_tasks) == 0


class TestCreateTaskMap:
    def test_create_task_map(self):
        tasks = [MagicMock(display_name=f"name{i}") for i in range(7)]

        mapped_tasks = under_test._create_task_map(tasks)

        for task in tasks:
            assert mapped_tasks[task.display_name] is not None
            assert mapped_tasks[task.display_name] == task


class TestIsTaskAFlip:
    def test_non_activated_task_is_not_a_flip(self):
        mock_task = _mock_task(activated=False)

        assert not under_test._is_task_a_flip(mock_task, {}, {})

    def test_not_a_success_or_failed_status_is_not_a_flip(self):
        mock_task = _mock_task(activated=True, status="started")

        assert not under_test._is_task_a_flip(mock_task, {}, {})

    def test_no_previous_task_is_not_a_flip(self):
        mock_task = _mock_task(activated=True, status="success")
        mock_task.is_success.return_value = False

        assert not under_test._is_task_a_flip(mock_task, {}, {})

    def test_no_next_task_is_not_a_flip(self):
        mock_task = _mock_task(activated=True, status="success")
        mock_task.is_success.return_value = False

        mock_prev_task = _mock_task(activated=True, status=mock_task.status)
        tasks_prev = {mock_task.display_name: mock_prev_task}

        assert not under_test._is_task_a_flip(mock_task, tasks_prev, {})

    def test_all_statuses_same_is_no_flip(self):
        mock_task = _mock_task(activated=True, status="failed")
        mock_task.is_success.return_value = False

        mock_prev_task = _mock_task(activated=True, status=mock_task.status)
        tasks_prev = {mock_task.display_name: mock_prev_task}

        mock_next_task = _mock_task(activated=True, status=mock_task.status)
        tasks_next = {mock_task.display_name: mock_next_task}

        assert not under_test._is_task_a_flip(mock_task, tasks_prev, tasks_next)

    def test_next_and_current_same_status_is_a_flip(self):
        mock_task = _mock_task(activated=True, status="failed")
        mock_task.is_success.return_value = False

        mock_prev_task = _mock_task(activated=True, status="success")
        tasks_prev = {mock_task.display_name: mock_prev_task}

        mock_next_task = _mock_task(activated=True, status=mock_task.status)
        tasks_next = {mock_task.display_name: mock_next_task}

        assert under_test._is_task_a_flip(mock_task, tasks_prev, tasks_next)

        mock_task = _mock_task(activated=True, status="success")
        mock_task.is_success.return_value = False

        mock_prev_task = _mock_task(activated=True, status="failed")
        tasks_prev = {mock_task.display_name: mock_prev_task}

        mock_next_task = _mock_task(activated=True, status=mock_task.status)
        tasks_next = {mock_task.display_name: mock_next_task}

        assert under_test._is_task_a_flip(mock_task, tasks_prev, tasks_next)

    def test_prev_task_not_activated_is_not_a_flip(self):
        mock_task = _mock_task(activated=True, status="failed")
        mock_task.is_success.return_value = False

        mock_prev_task = _mock_task(activated=False, status="success")
        tasks_prev = {mock_task.display_name: mock_prev_task}

        mock_next_task = _mock_task(activated=True, status=mock_task.status)
        tasks_next = {mock_task.display_name: mock_next_task}

        assert not under_test._is_task_a_flip(mock_task, tasks_prev, tasks_next)

    def test_next_task_not_activated_is_not_a_flip(self):
        mock_task = _mock_task(activated=True, status="failed")
        mock_task.is_success.return_value = False

        mock_prev_task = _mock_task(activated=True, status="success")
        tasks_prev = {mock_task.display_name: mock_prev_task}

        mock_next_task = _mock_task(activated=False, status=mock_task.status)
        tasks_next = {mock_task.display_name: mock_next_task}

        assert not under_test._is_task_a_flip(mock_task, tasks_prev, tasks_next)

    def test_prev_and_current_same_status_is_not_a_flip(self):
        mock_task = _mock_task(activated=True, status="failed")
        mock_task.is_success.return_value = False

        mock_prev_task = _mock_task(activated=True, status=mock_task.status)
        tasks_prev = {mock_task.display_name: mock_prev_task}

        mock_next_task = _mock_task(activated=True, status="success")
        tasks_next = {mock_task.display_name: mock_next_task}

        assert not under_test._is_task_a_flip(mock_task, tasks_prev, tasks_next)


class TestMeaningfulTaskStatus:
    def test_success_failed_status_pass(self):
        pass_mock = MagicMock(status="success")

        assert under_test._check_meaningful_task_status(pass_mock)

        failed_mock = MagicMock(status="failed")

        assert under_test._check_meaningful_task_status(failed_mock)

    def test_other_task_status_do_not_pass(self):
        task_mock = MagicMock(status="started")

        assert not under_test._check_meaningful_task_status(task_mock)


def _mock_task(activated: bool = None, status: str = None, display_name: str = None):
    return MagicMock(activated=activated, status=status, display_name=display_name)
