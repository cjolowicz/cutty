"""Utilities for template variables."""
import json
from pathlib import Path
from typing import Any

from cutty.projects.config import readprojectconfigfile
from tests.util.git import updatefile


def projectvariable(project: Path, name: str) -> Any:
    """Return the bound value of a project variable."""
    config = readprojectconfigfile(project)
    return next(binding.value for binding in config.bindings if binding.name == name)


def templatevariable(template: Path, name: str) -> Any:
    """Return the value of a template variable."""
    path = template / "cookiecutter.json"
    data = json.loads(path.read_text())
    return data[name]


def updatetemplatevariable(template: Path, name: str, value: Any) -> None:
    """Add or update a template variable."""
    path = template / "cookiecutter.json"
    data = json.loads(path.read_text())
    data[name] = value
    updatefile(path, json.dumps(data))
