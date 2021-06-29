"""Unit tests for cutty.filestorage.adapters.git."""
import pathlib

import pygit2
import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.git import GitRepositoryObserver
from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.domain.purepath import PurePath


@pytest.fixture
def project(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture for a project path."""
    return tmp_path / "project"


@pytest.fixture
def storage(project: pathlib.Path) -> DiskFileStorage:
    """Fixture for a storage."""
    observer = GitRepositoryObserver(project=project)
    storage = DiskFileStorage(project.parent)
    storage.observers.append(observer)
    return storage


@pytest.fixture
def file(project: pathlib.Path) -> RegularFile:
    """Fixture for a regular file."""
    path = PurePath(project.name, "README.md")
    return RegularFile(path, b"")


def test_repository(
    storage: DiskFileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It creates a repository."""
    with storage:
        storage.add(file)

    pygit2.Repository(project)  # does not raise


def test_commit(
    storage: DiskFileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It creates a commit."""
    with storage:
        storage.add(file)

    repository = pygit2.Repository(project)
    repository.head  # does not raise


def test_index(
    storage: DiskFileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It updates the index."""
    with storage:
        storage.add(file)

    repository = pygit2.Repository(project)
    assert file.path.name in repository.index


def test_hook_edits(
    storage: DiskFileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It commits file modifications applied by hooks."""
    with storage:
        storage.add(file)
        (project / file.path.name).write_bytes(b"teapot")

    repository = pygit2.Repository(project)
    blob = repository.head.peel().tree / file.path.name
    assert b"teapot" == blob.data


def test_hook_deletes(
    storage: DiskFileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It does not commit files deleted by hooks."""
    with storage:
        storage.add(file)
        (project / file.path.name).unlink()

    repository = pygit2.Repository(project)
    assert file.path.name not in repository.head.peel().tree


def test_hook_additions(storage: DiskFileStorage, project: pathlib.Path) -> None:
    """It commits files created by hooks."""
    with storage:
        project.mkdir()
        (project / "marker").touch()

    repository = pygit2.Repository(project)
    assert "marker" in repository.head.peel().tree
