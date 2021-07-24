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


def test_readprojectconfigfile(
    storage: DiskFileStorage, projectconfig: ProjectConfig
) -> None:
    """It returns the persisted Cookiecutter context."""
    file = createprojectconfigfile(PurePath(), projectconfig)

    with storage:
        storage.add(file)

    assert projectconfig == readprojectconfigfile(storage.root)


def test_readprojectconfigfile_template_typeerror(tmp_path: pathlib.Path) -> None:
    """It checks that `_template` key is a string."""
    template = None
    text = json.dumps({"_template": template})
    (tmp_path / PROJECT_CONFIG_FILE).write_text(text)

    with pytest.raises(TypeError):
        readprojectconfigfile(tmp_path)
