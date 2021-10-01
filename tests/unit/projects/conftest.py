"""Fixtures for cutty.projects."""
import pathlib

import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path as VirtualPath
from cutty.filesystems.domain.purepath import PurePath
from cutty.projects.common import GenerateProject
from cutty.services.loadtemplate import Template
from cutty.services.loadtemplate import TemplateMetadata


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
def template() -> Template:
    """Fixture for a `Template` instance."""
    templatepath = VirtualPath(filesystem=DictFilesystem({}))
    location = "https://example.com/template"
    metadata = TemplateMetadata(location, None, None, "template", None)
    return Template(metadata, templatepath)


@pytest.fixture
def generateproject() -> GenerateProject:
    """Fixture for a `generateproject` function."""

    def _(project: pathlib.Path) -> None:
        (project / "cutty.json").touch()

    return _
