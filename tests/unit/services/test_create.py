"""Unit tests for cutty.services.create."""
import dataclasses
import pathlib

import pygit2
import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path as VirtualPath
from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.create import creategitrepository
from cutty.services.create import LATEST_BRANCH
from cutty.util.git import Repository


@pytest.fixture
def projectpath(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture for a project path."""
    return tmp_path / "project"


@pytest.fixture
def storage(projectpath: pathlib.Path) -> FileStorage:
    """Fixture for a storage."""
    return DiskFileStorage(projectpath.parent)


@pytest.fixture
def file(projectpath: pathlib.Path) -> RegularFile:
    """Fixture for a regular file."""
    path = PurePath(projectpath.name, "README.md")
    return RegularFile(path, b"")


@pytest.fixture
def project2(
    storage: FileStorage, file: RegularFile, projectpath: pathlib.Path
) -> pathlib.Path:
    """Fixture for a project path."""
    with storage:
        storage.add(file)

    return projectpath


@pytest.fixture
def template() -> Template:
    """Fixture for a `Template` instance."""
    templatepath = VirtualPath(filesystem=DictFilesystem({}))
    return Template("template", templatepath, None)


def test_repository(project2: pathlib.Path, template: Template) -> None:
    """It creates a repository."""
    creategitrepository(project2, template)

    Repository.open(project2)  # does not raise


def test_commit(project2: pathlib.Path, template: Template) -> None:
    """It creates a commit."""
    creategitrepository(project2, template)

    repository = Repository.open(project2)
    repository.head.commit  # does not raise


def test_commit_message_template(project2: pathlib.Path, template: Template) -> None:
    """It includes the template name in the commit message."""
    creategitrepository(project2, template)

    repository = Repository.open(project2)
    assert template.name in repository.head.commit.message


def test_commit_message_revision(project2: pathlib.Path, template: Template) -> None:
    """It includes the revision in the commit message."""
    template = dataclasses.replace(template, revision="1.0.0")
    creategitrepository(project2, template)

    repository = Repository.open(project2)
    assert template.revision in repository.head.commit.message


def tree(repository: Repository) -> pygit2.Tree:
    """Return the tree at the HEAD of the repository."""
    return repository.head.commit.tree


def test_existing_repository(
    storage: FileStorage,
    file: RegularFile,
    projectpath: pathlib.Path,
    template: Template,
) -> None:
    """It creates the commit in an existing repository."""
    repository = Repository.init(projectpath)
    repository.commit()

    with storage:
        storage.add(file)

    creategitrepository(projectpath, template)

    assert file.path.name in tree(repository)


def test_branch(project2: pathlib.Path, template: Template) -> None:
    """It creates a branch pointing to the initial commit."""
    creategitrepository(project2, template)

    repository = Repository.open(project2)
    assert repository.head.commit == repository.heads[LATEST_BRANCH]


def test_branch_not_checked_out(project2: pathlib.Path, template: Template) -> None:
    """It does not check out the `latest` branch."""
    creategitrepository(project2, template)

    repository = Repository.open(project2)
    assert repository.head.name != LATEST_BRANCH
