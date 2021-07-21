"""Unit tests for cutty.templates.adapters.cookiecutter.projectconfig."""
import json

from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.adapters.cookiecutter.projectconfig import createprojectconfigfile
from cutty.templates.domain.bindings import Binding


def test_createprojectconfigfile() -> None:
    """It creates a JSON file with the settings and bindings."""
    project = PurePath("example")
    settings = {
        "_template": "https://example.com/repository.git",
        "_extensions": ["jinja2_time.TimeExtension"],
    }
    bindings = [Binding("project", "example"), Binding("license", "MIT")]

    file = createprojectconfigfile(project, settings, bindings)

    data = json.loads(file.blob.decode())
    assert data.keys() == settings.keys() | {binding.name for binding in bindings}
