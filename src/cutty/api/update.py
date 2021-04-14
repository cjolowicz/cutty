"""Update a project."""
from pathlib import Path
from typing import Optional

from ..core.application import Application
from ..core.project import Project


def update(
    *,
    interactive: bool = False,
    revision: Optional[str] = None,
    directory: Optional[Path] = None,
    config_file: Optional[Path] = None,
) -> None:
    """Update a project from a Cookiecutter template."""
    application = Application.create(config_file=config_file)
    project = Project.load(Path.cwd())

    application.update_project(
        project, directory=directory, revision=revision, interactive=interactive
    )
