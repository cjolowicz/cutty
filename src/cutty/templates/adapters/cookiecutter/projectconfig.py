"""Configuration for projects generated from Cookiecutter templates."""
import json
import pathlib
from dataclasses import dataclass
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
    data = {
        "template": {"location": config.template},
        "bindings": {binding.name: binding.value for binding in config.bindings},
    }
    blob = json.dumps(data).encode()

    return RegularFile(path, blob)


def readprojectconfigfile(project: pathlib.Path) -> ProjectConfig:
    """Load the project configuration."""
    path = project / PROJECT_CONFIG_FILE
    text = path.read_text()
    data = json.loads(text)

    if not isinstance(data, dict):
        raise TypeError(f"{path}: project configuration must be 'dict', got {data!r}")

    context = {key: value for key, value in data.items()}
    template = context["template"]["location"]

    if not isinstance(template, str):
        raise TypeError(f"{path}: template location must be 'str', got {template!r}")

    bindings = [Binding(key, value) for key, value in context["bindings"].items()]

    return ProjectConfig(template, bindings)
