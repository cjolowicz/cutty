"""Unit tests for cutty.projects.create."""
import dataclasses
import pathlib

import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.purepath import PurePath
from cutty.projects.repository import LATEST_BRANCH
from cutty.projects.repository import ProjectRepository
from cutty.projects.template import Template
from cutty.util.git import Repository


def creategitrepository(projectdir: pathlib.Path, template: Template.Metadata) -> None:
    """Initialize the git repository for a project."""
    ProjectRepository.create(projectdir, template)


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
def project(
    storage: FileStorage, file: RegularFile, projectpath: pathlib.Path
) -> pathlib.Path:
    """Fixture for a project path."""
    with storage:
        storage.add(file)

    return projectpath


def test_repository(project: pathlib.Path, template: Template.Metadata) -> None:
    """It creates a repository."""
    creategitrepository(project, template)

    Repository.open(project)  # does not raise


def test_commit(project: pathlib.Path, template: Template.Metadata) -> None:
    """It creates a commit."""
    creategitrepository(project, template)

    repository = Repository.open(project)
    repository.head.commit  # does not raise


def test_commit_message_template(
    project: pathlib.Path, template: Template.Metadata
) -> None:
    """It includes the template name in the commit message."""
    creategitrepository(project, template)

    repository = Repository.open(project)
    assert template.name in repository.head.commit.message


def test_commit_message_revision(
    project: pathlib.Path, template: Template.Metadata
) -> None:
    """It includes the revision in the commit message."""
    template = dataclasses.replace(template, revision="1.0.0")
    creategitrepository(project, template)

    repository = Repository.open(project)
    assert template.revision in repository.head.commit.message


def test_existing_repository(
    storage: FileStorage,
    file: RegularFile,
    projectpath: pathlib.Path,
    template: Template.Metadata,
) -> None:
    """It creates the commit in an existing repository."""
    repository = Repository.init(projectpath)
    repository.commit()

    with storage:
        storage.add(file)

    creategitrepository(projectpath, template)

    assert file.path.name in repository.head.commit.tree


def test_branch(project: pathlib.Path, template: Template.Metadata) -> None:
    """It creates a branch pointing to the initial commit."""
    creategitrepository(project, template)

    repository = Repository.open(project)
    assert repository.head.commit == repository.heads[LATEST_BRANCH]


def test_branch_not_checked_out(
    project: pathlib.Path, template: Template.Metadata
) -> None:
    """It does not check out the `latest` branch."""
    creategitrepository(project, template)

    repository = Repository.open(project)
    assert repository.head.name != LATEST_BRANCH
