"""Unit tests for cutty.templates.adapters.cookiecutter.projectconfig."""
import dataclasses
import json
import pathlib

import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.adapters.cookiecutter.projectconfig import createprojectconfigfile
from cutty.templates.adapters.cookiecutter.projectconfig import ProjectConfig
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.templates.domain.bindings import Binding


@pytest.fixture
def projectconfig() -> ProjectConfig:
    """Fixture for a project configuration."""
    template = "https://example.com/repository.git"
    bindings = [Binding("project", "example"), Binding("license", "MIT")]

    return ProjectConfig(template, bindings)


@pytest.fixture
def storage(tmp_path: pathlib.Path) -> DiskFileStorage:
    """Fixture for disk file storage."""
    return DiskFileStorage(tmp_path / "storage")


def test_roundtrip(storage: DiskFileStorage, projectconfig: ProjectConfig) -> None:
    """It returns the persisted project configuration."""
    file = createprojectconfigfile(PurePath(), projectconfig)

    with storage:
        storage.add(file)

    assert projectconfig == readprojectconfigfile(storage.root)


def test_readprojectconfigfile_typeerror(
    storage: DiskFileStorage, projectconfig: ProjectConfig
) -> None:
    """It checks that the template location is a string."""
    file = createprojectconfigfile(PurePath(), projectconfig)
    file = dataclasses.replace(file, blob=json.dumps("teapot").encode())

    with storage:
        storage.add(file)

    with pytest.raises(TypeError):
        readprojectconfigfile(storage.root)


def test_readprojectconfigfile_template_typeerror(
    storage: DiskFileStorage, projectconfig: ProjectConfig
) -> None:
    """It checks that the template location is a string."""
    file = createprojectconfigfile(PurePath(), projectconfig)

    # Replace the template location with `None` in the JSON record.
    data = json.loads(file.blob.decode())
    data["template"]["location"] = None
    file = dataclasses.replace(file, blob=json.dumps(data).encode())

    with storage:
        storage.add(file)

    with pytest.raises(TypeError):
        readprojectconfigfile(storage.root)
