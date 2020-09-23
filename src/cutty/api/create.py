"""Create a project."""
from pathlib import Path
from typing import Optional

from ..core.application import Application
from ..core.project import Project


def create(
    location: str,
    *,
    interactive: bool = True,
    revision: Optional[str] = None,
    directory: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    config_file: Optional[Path] = None,
) -> None:
    """Create a project from a Cookiecutter template."""
    application = Application.create(config_file=config_file)

    with application.load_template(
        location, directory=directory, revision=revision
    ) as template:
        path = application.generate_project(
            template, output_dir=output_dir, interactive=interactive
        )

        Project.create(path, name=template.name, version=template.version)
