"""Unit tests for cutty.projects.create."""
import dataclasses
import pathlib

import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path as VirtualPath
from cutty.filesystems.domain.purepath import PurePath
from cutty.projects.common import LATEST_BRANCH
from cutty.projects.create import creategitrepository2
from cutty.services.loadtemplate import Template as Template2
from cutty.services.loadtemplate import TemplateMetadata
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
def project(
    storage: FileStorage, file: RegularFile, projectpath: pathlib.Path
) -> pathlib.Path:
    """Fixture for a project path."""
    with storage:
        storage.add(file)

    return projectpath


@pytest.fixture
def template2() -> Template2:
    """Fixture for a `Template` instance."""
    templatepath = VirtualPath(filesystem=DictFilesystem({}))
    location = "https://example.com/template"
    metadata = TemplateMetadata(location, None, None, "template", None)
    return Template2(metadata, templatepath)


def test_repository(project: pathlib.Path, template2: Template2) -> None:
    """It creates a repository."""
    creategitrepository2(project, template2)

    Repository.open(project)  # does not raise


def test_commit(project: pathlib.Path, template2: Template2) -> None:
    """It creates a commit."""
    creategitrepository2(project, template2)

    repository = Repository.open(project)
    repository.head.commit  # does not raise


def test_commit_message_template(project: pathlib.Path, template2: Template2) -> None:
    """It includes the template name in the commit message."""
    creategitrepository2(project, template2)

    repository = Repository.open(project)
    assert template2.metadata.name in repository.head.commit.message


def test_commit_message_revision(project: pathlib.Path, template2: Template2) -> None:
    """It includes the revision in the commit message."""
    template2 = dataclasses.replace(
        template2, metadata=dataclasses.replace(template2.metadata, revision="1.0.0")
    )
    creategitrepository2(project, template2)

    repository = Repository.open(project)
    assert template2.metadata.revision in repository.head.commit.message


def test_existing_repository(
    storage: FileStorage,
    file: RegularFile,
    projectpath: pathlib.Path,
    template2: Template2,
) -> None:
    """It creates the commit in an existing repository."""
    repository = Repository.init(projectpath)
    repository.commit()

    with storage:
        storage.add(file)

    creategitrepository2(projectpath, template2)

    assert file.path.name in repository.head.commit.tree


def test_branch(project: pathlib.Path, template2: Template2) -> None:
    """It creates a branch pointing to the initial commit."""
    creategitrepository2(project, template2)

    repository = Repository.open(project)
    assert repository.head.commit == repository.heads[LATEST_BRANCH]


def test_branch_not_checked_out(project: pathlib.Path, template2: Template2) -> None:
    """It does not check out the `latest` branch."""
    creategitrepository2(project, template2)

    repository = Repository.open(project)
    assert repository.head.name != LATEST_BRANCH
