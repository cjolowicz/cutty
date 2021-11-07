"""Configuration for projects generated from templates."""
import json
import pathlib
from dataclasses import dataclass
from typing import Optional
from typing import Sequence

from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.domain.purepath import PurePath
from cutty.variables.domain.bindings import Binding


PROJECT_CONFIG_FILE = "cutty.json"
COOKIECUTTER_JSON_FILE = ".cookiecutter.json"


@dataclass(frozen=True)
class ProjectConfig:
    """Project configuration."""

    template: str
    bindings: Sequence[Binding]
    revision: Optional[str]
    directory: Optional[pathlib.Path] = None


def createprojectconfigfile(project: PurePath, config: ProjectConfig) -> RegularFile:
    """Create a JSON file with the settings and bindings for a project."""
    directory = str(config.directory) if config.directory is not None else None
    path = project / PROJECT_CONFIG_FILE
    data = {
        "template": {
            "location": config.template,
            "revision": config.revision,
            "directory": directory,
        },
        "bindings": {binding.name: binding.value for binding in config.bindings},
    }
    text = json.dumps(data, indent=2) + "\n"

    return RegularFile(path, text.encode())


def readprojectconfigfile(project: pathlib.Path) -> ProjectConfig:
    """Load the project configuration."""
    path = project / PROJECT_CONFIG_FILE
    text = path.read_text()
    data = json.loads(text)

    if not isinstance(data, dict):
        raise TypeError(f"{path}: project configuration must be 'dict', got {data!r}")

    template = data["template"]["location"]

    if not isinstance(template, str):
        raise TypeError(f"{path}: template location must be 'str', got {template!r}")

    directory = data["template"]["directory"]

    if not (directory is None or isinstance(directory, str)):
        raise TypeError(
            f"{path}: template directory must be 'str' or 'None', got {directory!r}"
        )

    revision = data["template"]["revision"]

    if not (revision is None or isinstance(revision, str)):
        raise TypeError(
            f"{path}: template revision must be 'str' or 'None', got {revision!r}"
        )

    bindings = [Binding(key, value) for key, value in data["bindings"].items()]

    return ProjectConfig(
        template,
        bindings,
        revision=revision,
        directory=pathlib.Path(directory) if directory is not None else None,
    )


def readcookiecutterjson(project: pathlib.Path) -> ProjectConfig:
    """Load the project configuration from a .cookiecutter.json file."""
    path = project / COOKIECUTTER_JSON_FILE
    text = path.read_text()
    data = json.loads(text)

    template = data.pop("_template")
    bindings = [Binding(name, value) for name, value in data.items()]

    return ProjectConfig(template, bindings, revision=None)
