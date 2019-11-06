import git
import os

from unittest.mock import MagicMock
from tempfile import TemporaryDirectory
import selectedtests.git_helper as under_test


def initialize_temp_repo(directory):
    repo = git.Repo.init(directory)
    repo.index.commit("initial commit -- no files changed")
    return repo


def repo_with_many_changed_files(temp_directory):
    repo = initialize_temp_repo(temp_directory)

    unchanged_file = os.path.join(temp_directory, "unchanged-file")
    file_to_delete = os.path.join(temp_directory, "file-to-delete")
    file_to_modify = os.path.join(temp_directory, "file-to-modify")
    file_to_rename = os.path.join(temp_directory, "file-to-rename")
    open(unchanged_file, "wb").close()
    open(file_to_delete, "wb").close()
    open(file_to_modify, "wb").close()
    open(file_to_rename, "wb").close()
    repo.index.add([unchanged_file, file_to_delete, file_to_modify, file_to_rename])
    repo.index.commit("add files to change")

    # rename file
    renamed_file = os.path.join(temp_directory, "now-renamed-file")
    os.rename(file_to_rename, renamed_file)

    # add new file
    new_file = os.path.join(temp_directory, "new-file")
    open(new_file, "wb").close()

    # modify file
    os.system(f"echo 'Added another line to modified_file' >> { file_to_modify }")

    # delete file
    os.remove(file_to_delete)
    repo.index.remove([file_to_delete], working_tree=True)

    # commit changes
    repo.index.add([unchanged_file, renamed_file, new_file, file_to_modify])
    repo.index.commit("add new file, modified file, and renamed file")

    return repo


class TestModifiedFilesForCommit:
    def test_added_modified_renamed_and_deleted_files(self):
        with TemporaryDirectory() as tmpdir:
            repo = repo_with_many_changed_files(tmpdir)
            most_recent_commit = repo.head.commit
            log_mock = MagicMock()
            modified_files = under_test.modified_files_for_commit(most_recent_commit, log_mock)
            assert "file-to-delete" in modified_files
            assert "file-to-modify" in modified_files
            assert "new-file" in modified_files
            assert "now-renamed-file" in modified_files
            assert "file-to-rename" not in modified_files
            assert "unchanged-file" not in modified_files
