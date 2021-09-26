"""Unit tests for cutty.services.create."""
import pathlib

import pygit2
import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.purepath import PurePath
from cutty.services.create import creategitrepository
from cutty.services.create import LATEST_BRANCH
from cutty.services.create import UPDATE_BRANCH
from cutty.util.git import Repository
from tests.util.git import createbranches


@pytest.fixture
def project(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture for a project path."""
    return tmp_path / "project"


@pytest.fixture
def storage(project: pathlib.Path) -> FileStorage:
    """Fixture for a storage."""
    return DiskFileStorage(project.parent)


@pytest.fixture
def file(project: pathlib.Path) -> RegularFile:
    """Fixture for a regular file."""
    path = PurePath(project.name, "README.md")
    return RegularFile(path, b"")


def test_repository(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It creates a repository."""
    with storage:
        storage.add(file)

    creategitrepository(project, "template", None)

    Repository.open(project)  # does not raise


def test_commit(storage: FileStorage, file: RegularFile, project: pathlib.Path) -> None:
    """It creates a commit."""
    with storage:
        storage.add(file)

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    repository.head.commit  # does not raise


def test_commit_message_template(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It includes the template name in the commit message."""
    with storage:
        storage.add(file)

    template = "awesome-template"
    creategitrepository(project, template, None)

    repository = Repository.open(project)
    assert template in repository.head.commit.message


def test_commit_message_revision(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It includes the revision in the commit message."""
    with storage:
        storage.add(file)

    revision = "1.0.0"
    creategitrepository(project, "template", revision)

    repository = Repository.open(project)
    assert revision in repository.head.commit.message


def test_index(storage: FileStorage, file: RegularFile, project: pathlib.Path) -> None:
    """It updates the index."""
    with storage:
        storage.add(file)

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    assert file.path.name in repository._repository.index


def tree(repository: Repository) -> pygit2.Tree:
    """Return the tree at the HEAD of the repository."""
    return repository.head.commit.tree


def test_hook_edits(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It commits file modifications applied by hooks."""
    with storage:
        storage.add(file)
        (project / file.path.name).write_bytes(b"teapot")

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    blob = tree(repository) / file.path.name
    assert b"teapot" == blob.data


def test_hook_deletes(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It does not commit files deleted by hooks."""
    with storage:
        storage.add(file)
        (project / file.path.name).unlink()

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    assert file.path.name not in tree(repository)


def test_hook_additions(storage: FileStorage, project: pathlib.Path) -> None:
    """It commits files created by hooks."""
    with storage:
        project.mkdir()
        (project / "marker").touch()

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    assert "marker" in tree(repository)


def test_existing_repository(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It creates the commit in an existing repository."""
    repository = Repository.init(project)
    repository.commit()

    with storage:
        storage.add(file)

    creategitrepository(project, "template", None)

    assert file.path.name in tree(repository)


def test_branch(storage: FileStorage, file: RegularFile, project: pathlib.Path) -> None:
    """It creates a branch pointing to the initial commit."""
    with storage:
        storage.add(file)

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    assert repository.head.commit == repository.heads[LATEST_BRANCH]


def test_branch_not_checked_out(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It does not check out the `latest` branch."""
    with storage:
        storage.add(file)

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    assert repository.head.name != LATEST_BRANCH


def test_existing_branch(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It updates the `update` branch if it exists."""
    repository = Repository.init(project)
    repository.commit()

    branch = repository.heads.create(UPDATE_BRANCH)
    repository.checkout(branch)

    with storage:
        storage.add(file)

    creategitrepository(project, "template", None)

    assert file.path.name in tree(repository)


def test_existing_branch_not_head(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It raises an exception if `update` exists but HEAD points elsewhere."""
    repository = Repository.init(project)
    repository.commit()

    repository.heads.create(UPDATE_BRANCH)

    with pytest.raises(Exception):
        with storage:
            storage.add(file)

        creategitrepository(project, "template", None)

    assert file.path.name not in tree(repository)


def test_existing_branch_commit_message(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It uses a different commit message on updates."""
    repository = Repository.init(project)
    repository.commit()

    update, _ = createbranches(repository, UPDATE_BRANCH, LATEST_BRANCH)
    repository.checkout(update)

    with storage:
        storage.add(file)

    creategitrepository(project, "template", None)

    assert "initial" not in repository.head.commit.message.lower()


def test_existing_branch_commit_message_template(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It includes the template name in the commit message."""
    repository = Repository.init(project)
    repository.commit()

    update, _ = createbranches(repository, UPDATE_BRANCH, LATEST_BRANCH)
    repository.checkout(update)

    with storage:
        storage.add(file)

    template = "awesome-template"
    creategitrepository(project, template, None)

    assert template in repository.head.commit.message


def test_existing_branch_commit_message_revision(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It includes the revision in the commit message."""
    repository = Repository.init(project)
    repository.commit()

    update, _ = createbranches(repository, UPDATE_BRANCH, LATEST_BRANCH)
    repository.checkout(update)

    with storage:
        storage.add(file)

    revision = "1.0.0"
    creategitrepository(project, "template", revision)

    assert revision in repository.head.commit.message


def test_existing_branch_no_changes(
    storage: FileStorage, project: pathlib.Path
) -> None:
    """It does not create an empty commit."""
    repository = Repository.init(project)
    repository.commit()

    branch = repository.heads.create(UPDATE_BRANCH)
    repository.checkout(branch)
    oldhead = repository.head.commit

    with storage:
        pass

    creategitrepository(project, "template", None)

    assert oldhead == repository.head.commit
