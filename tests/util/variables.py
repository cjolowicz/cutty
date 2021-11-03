"""Utilities for template variables."""
from pathlib import Path
from typing import Any

from cutty.projects.config import readprojectconfigfile


def projectvariable(project: Path, name: str) -> Any:
    """Return the bound value of a project variable."""
    config = readprojectconfigfile(project)
    return next(binding.value for binding in config.bindings if binding.name == name)
