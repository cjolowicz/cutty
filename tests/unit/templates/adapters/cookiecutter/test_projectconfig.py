"""Unit tests for cutty.templates.adapters.cookiecutter.projectconfig."""
import json
import pathlib

import pytest

from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.adapters.cookiecutter.projectconfig import createprojectconfigfile
from cutty.templates.adapters.cookiecutter.projectconfig import PROJECT_CONFIG_FILE
from cutty.templates.adapters.cookiecutter.projectconfig import ProjectConfig
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile2
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


def test_readprojectconfigfile(tmp_path: pathlib.Path) -> None:
    """It returns the persisted Cookiecutter context."""
    template = "https://example.com/repository.git"
    bindings = [Binding("project", "example")]
    config = ProjectConfig(template, bindings)
    file = createprojectconfigfile(PurePath(), config)
    tmp_path.joinpath(*file.path.parts).write_bytes(file.blob)

    assert config == readprojectconfigfile2(tmp_path)


def test_getprojecttemplate(tmp_path: pathlib.Path) -> None:
    """It returns the `_template` key from cutty.json."""
    template = "https://example.com/repository.git"
    text = json.dumps({"_template": template})
    (tmp_path / PROJECT_CONFIG_FILE).write_text(text)

    assert template == readprojectconfigfile2(tmp_path).template


def test_getprojecttemplate_typeerror(tmp_path: pathlib.Path) -> None:
    """It checks that `_template` key is a string."""
    template = None
    text = json.dumps({"_template": template})
    (tmp_path / PROJECT_CONFIG_FILE).write_text(text)

    with pytest.raises(TypeError):
        readprojectconfigfile2(tmp_path).template
