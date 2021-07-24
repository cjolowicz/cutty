"""Configuration for projects generated from Cookiecutter templates."""
import json
import pathlib
from dataclasses import dataclass
from typing import Sequence

from cutty.filestorage.domain.files import loadfile
from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.path import Path
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


def readprojectconfigfile(project: pathlib.Path) -> ProjectConfig:
    """Load the project configuration."""
    path = Path(filesystem=DiskFilesystem(project))
    file = loadfile(path / PROJECT_CONFIG_FILE)

    assert isinstance(file, RegularFile)  # noqa: S101

    data = json.loads(file.blob.decode())
    context = {key: value for key, value in data.items()}
    template = context.pop("_template")

    if not isinstance(template, str):
        raise TypeError(f"{project}: _template must be 'str', got {template!r}")

    bindings = [Binding(key, value) for key, value in context.items()]

    return ProjectConfig(template, bindings)
