"""Unit tests for cutty.filestorage.adapters.observers.git."""
import pathlib

import pygit2
import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.observers.git import commit as _commit
from cutty.filestorage.adapters.observers.git import GitRepositoryObserver
from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.observers import observe
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.purepath import PurePath


@pytest.fixture
def project(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture for a project path."""
    return tmp_path / "project"


@pytest.fixture
def storage(project: pathlib.Path) -> FileStorage:
    """Fixture for a storage."""
    observer = GitRepositoryObserver(project=project)
    storage = DiskFileStorage(project.parent)
    return observe(storage, observer)


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

    pygit2.Repository(project)  # does not raise


def test_commit(storage: FileStorage, file: RegularFile, project: pathlib.Path) -> None:
    """It creates a commit."""
    with storage:
        storage.add(file)

    repository = pygit2.Repository(project)
    repository.head  # does not raise


def test_index(storage: FileStorage, file: RegularFile, project: pathlib.Path) -> None:
    """It updates the index."""
    with storage:
        storage.add(file)

    repository = pygit2.Repository(project)
    assert file.path.name in repository.index


def tree(repository: pygit2.Repository) -> pygit2.Tree:
    """Return the tree at the HEAD of the repository."""
    return repository.head.peel().tree


def test_hook_edits(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It commits file modifications applied by hooks."""
    with storage:
        storage.add(file)
        (project / file.path.name).write_bytes(b"teapot")

    repository = pygit2.Repository(project)
    blob = tree(repository) / file.path.name
    assert b"teapot" == blob.data


def test_hook_deletes(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It does not commit files deleted by hooks."""
    with storage:
        storage.add(file)
        (project / file.path.name).unlink()

    repository = pygit2.Repository(project)
    assert file.path.name not in tree(repository)


def test_hook_additions(storage: FileStorage, project: pathlib.Path) -> None:
    """It commits files created by hooks."""
    with storage:
        project.mkdir()
        (project / "marker").touch()

    repository = pygit2.Repository(project)
    assert "marker" in tree(repository)


def commit(repository: pygit2.Repository) -> None:
    """Create an initial empty commit."""
    signature = pygit2.Signature("you", "you@example.com")
    _commit(repository, message="Initial", signature=signature)


def test_existing_repository(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It creates the commit in an existing repository."""
    repository = pygit2.init_repository(project)
    commit(repository)

    with storage:
        storage.add(file)

    assert file.path.name in tree(repository)


def test_branch(storage: FileStorage, file: RegularFile, project: pathlib.Path) -> None:
    """It creates a branch pointing to the initial commit."""
    with storage:
        storage.add(file)

    repository = pygit2.Repository(project)
    reference = repository.references[f"refs/heads/{LATEST_BRANCH}"]
    assert repository.head.peel() == reference.peel()


def test_branch_not_checked_out(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It does not check out the `latest` branch."""
    with storage:
        storage.add(file)

    repository = pygit2.Repository(project)
    assert repository.references["HEAD"].target != f"refs/heads/{LATEST_BRANCH}"


def test_existing_branch(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It updates the `latest` branch if it exists."""
    repository = pygit2.init_repository(project)
    commit(repository)
    repository.branches.create(LATEST_BRANCH, repository.head.peel())
    repository.set_head(f"refs/heads/{LATEST_BRANCH}")

    with storage:
        storage.add(file)

    assert file.path.name in tree(repository)


def test_existing_branch_not_head(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It raises an exception if `latest` exists but HEAD points elsewhere."""
    repository = pygit2.init_repository(project)
    commit(repository)
    repository.branches.create(LATEST_BRANCH, repository.head.peel())

    with pytest.raises(Exception):
        with storage:
            storage.add(file)

    assert file.path.name not in tree(repository)


def test_existing_branch_commit_message(
    storage: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It uses a different commit message on updates."""
    repository = pygit2.init_repository(project)
    commit(repository)
    repository.branches.create(LATEST_BRANCH, repository.head.peel())
    repository.set_head(f"refs/heads/{LATEST_BRANCH}")

    with storage:
        storage.add(file)

    commit_ = repository.head.peel()
    assert "initial" not in commit_.message.lower()


def test_existing_branch_no_changes(
    storage: FileStorage, project: pathlib.Path
) -> None:
    """It does not create an empty commit."""
    repository = pygit2.init_repository(project)
    commit(repository)

    repository.branches.create(LATEST_BRANCH, repository.head.peel())
    repository.set_head(f"refs/heads/{LATEST_BRANCH}")
    oldhead = repository.head.target

    with storage:
        pass

    assert oldhead == repository.head.target
