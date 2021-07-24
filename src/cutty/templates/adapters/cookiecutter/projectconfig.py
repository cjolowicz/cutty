"""Configuration for projects generated from Cookiecutter templates."""
import json
import pathlib
from dataclasses import dataclass
from typing import Any
from typing import Sequence

from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.domain.bindings import Binding


PROJECT_CONFIG_FILE = "cutty.json"


@dataclass
class ProjectConfig:
    """Project configuration."""

    template: str
    bindings: Sequence[Binding]


def createprojectconfigfile(project: PurePath, config: ProjectConfig) -> RegularFile:
    """Create a JSON file with the settings and bindings for a project."""
    path = project / PROJECT_CONFIG_FILE
    data = {binding.name: binding.value for binding in config.bindings} | {
        "_template": config.template
    }
    blob = json.dumps(data).encode()

    return RegularFile(path, blob)


def readprojectconfigfile(project: pathlib.Path) -> dict[str, Any]:
    """Return the Cookiecutter context of the project."""
    text = (project / PROJECT_CONFIG_FILE).read_text()
    data = json.loads(text)
    return {key: value for key, value in data.items() if isinstance(key, str)}


def readprojectconfigfile2(project: pathlib.Path) -> ProjectConfig:
    """Load the project configuration."""
    context = readprojectconfigfile(project)
    template = context.pop("_template")

    if not isinstance(template, str):
        raise TypeError(f"{project}: _template must be 'str', got {template!r}")

    bindings = [Binding(key, value) for key, value in context.items()]

    return ProjectConfig(template, bindings)
