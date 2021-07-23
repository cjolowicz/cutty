"""Unit tests for cutty.templates.adapters.cookiecutter.projectconfig."""
import json
import pathlib

from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.adapters.cookiecutter.projectconfig import createprojectconfigfile
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.templates.domain.bindings import Binding


def test_createprojectconfigfile_bindings() -> None:
    """It creates a JSON file with the bindings."""
    template = "https://example.com/repository.git"
    project = PurePath("example")
    bindings = [Binding("project", "example"), Binding("license", "MIT")]

    file = createprojectconfigfile(project, bindings, template)

    data = json.loads(file.blob.decode())
    assert all(binding.name in data for binding in bindings)


def test_createprojectconfigfile_template() -> None:
    """It creates a JSON file containing the template location."""
    template = "https://example.com/repository.git"
    project = PurePath("example")
    bindings = [Binding("Project", "example")]

    file = createprojectconfigfile(project, bindings, template)

    assert "_template" in json.loads(file.blob.decode())


def test_readprojectconfigfile(tmp_path: pathlib.Path) -> None:
    """It returns the persisted Cookiecutter context."""
    context = {"project": "example"}
    text = json.dumps(context)
    (tmp_path / "cutty.json").write_text(text)

    assert context == readprojectconfigfile(tmp_path)
