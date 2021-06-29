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
