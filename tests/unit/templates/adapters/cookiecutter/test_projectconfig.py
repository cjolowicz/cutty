"""Unit tests for cutty.templates.adapters.cookiecutter.projectconfig."""
import json
import pathlib

import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.adapters.cookiecutter.projectconfig import createprojectconfigfile
from cutty.templates.adapters.cookiecutter.projectconfig import PROJECT_CONFIG_FILE
from cutty.templates.adapters.cookiecutter.projectconfig import ProjectConfig
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.templates.domain.bindings import Binding


def test_createprojectconfigfile_bindings() -> None:
    """It creates a JSON file with the bindings."""
    template = "https://example.com/repository.git"
    project = PurePath("example")
    bindings = [Binding("project", "example"), Binding("license", "MIT")]

    config = ProjectConfig(template, bindings)
    file = createprojectconfigfile(project, config)

    data = json.loads(file.blob.decode())
    assert all(binding.name in data for binding in bindings)


def test_createprojectconfigfile_template() -> None:
    """It creates a JSON file containing the template location."""
    template = "https://example.com/repository.git"
    project = PurePath("example")
    bindings = [Binding("Project", "example")]

    config = ProjectConfig(template, bindings)
    file = createprojectconfigfile(project, config)

    assert "_template" in json.loads(file.blob.decode())


@pytest.fixture
def storage(tmp_path: pathlib.Path) -> DiskFileStorage:
    """Fixture for disk file storage."""
    return DiskFileStorage(tmp_path / "storage")


def test_readprojectconfigfile(storage: DiskFileStorage) -> None:
    """It returns the persisted Cookiecutter context."""
    template = "https://example.com/repository.git"
    bindings = [Binding("project", "example")]
    config = ProjectConfig(template, bindings)
    file = createprojectconfigfile(PurePath(), config)

    with storage:
        storage.add(file)

    assert config == readprojectconfigfile(storage.root)


def test_readprojectconfigfile_template(storage: DiskFileStorage) -> None:
    """It returns the `_template` key from cutty.json."""
    template = "https://example.com/repository.git"
    bindings = [Binding("project", "example")]
    config = ProjectConfig(template, bindings)
    file = createprojectconfigfile(PurePath(), config)

    with storage:
        storage.add(file)

    config = readprojectconfigfile(storage.root)

    assert template == config.template


def test_readprojectconfigfile_template_typeerror(tmp_path: pathlib.Path) -> None:
    """It checks that `_template` key is a string."""
    template = None
    text = json.dumps({"_template": template})
    (tmp_path / PROJECT_CONFIG_FILE).write_text(text)

    with pytest.raises(TypeError):
        readprojectconfigfile(tmp_path)
