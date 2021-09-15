"""Unit tests for cutty.templates.adapters.cookiecutter.projectconfig."""
import dataclasses
import json
import pathlib

import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.adapters.cookiecutter.projectconfig import createprojectconfigfile
from cutty.templates.adapters.cookiecutter.projectconfig import (
    LEGACY_PROJECT_CONFIG_FILE,
)
from cutty.templates.adapters.cookiecutter.projectconfig import ProjectConfig
from cutty.templates.adapters.cookiecutter.projectconfig import readcookiecutterjson2
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.templates.domain.bindings import Binding


@pytest.fixture
def projectconfig() -> ProjectConfig:
    """Fixture for a project configuration."""
    template = "https://example.com/repository.git"
    bindings = [Binding("project", "example"), Binding("license", "MIT")]

    return ProjectConfig(template, bindings, directory=pathlib.PurePosixPath("a"))


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


def test_readprojectconfigfile_directory_typeerror(
    storage: DiskFileStorage, projectconfig: ProjectConfig
) -> None:
    """It checks that the template directory is a string or None."""
    file = createprojectconfigfile(PurePath(), projectconfig)

    # Replace the template location with 42 in the JSON record.
    data = json.loads(file.blob.decode())
    data["template"]["directory"] = 42
    file = dataclasses.replace(file, blob=json.dumps(data).encode())

    with storage:
        storage.add(file)

    with pytest.raises(TypeError):
        readprojectconfigfile(storage.root)


def test_createprojectconfigfile_format(
    storage: DiskFileStorage, projectconfig: ProjectConfig
) -> None:
    """It formats the JSON file in a standard way."""
    file = createprojectconfigfile(PurePath(), projectconfig)

    with storage:
        storage.add(file)

    path = storage.resolve(file.path)
    lines = path.read_text().splitlines(keepends=True)

    assert "{\n" == lines[0]
    assert lines[1].startswith('  "')
    assert lines[1].endswith('": {\n')
    assert "}\n" == lines[-1]


def createlegacyprojectconfigfile(
    project: PurePath, projectconfig: ProjectConfig
) -> RegularFile:
    """Create a .cookiecutter.json file."""
    data = {"_template": projectconfig.template} | {
        binding.name: binding.value for binding in projectconfig.bindings
    }

    path = project / LEGACY_PROJECT_CONFIG_FILE
    text = json.dumps(data, indent=4)

    return RegularFile(path, text.encode())


def test_readcookiecutterjson(
    storage: DiskFileStorage, projectconfig: ProjectConfig
) -> None:
    """It loads a project configuration from a .cookiecutter.json file."""
    # The .cookiecutter.json format does not include the template directory.
    projectconfig = dataclasses.replace(projectconfig, directory=None)

    file = createlegacyprojectconfigfile(PurePath(), projectconfig)

    with storage:
        storage.add(file)

    assert projectconfig == readcookiecutterjson2(storage.root)
