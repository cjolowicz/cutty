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

    with application.load_template_for_project(
        project, directory=directory, revision=revision
    ) as template:
        with project.update(name="template", version=template.version) as worktree:
            application.generate_project(
                template,
                output_dir=worktree.parent,
                interactive=interactive,
                overwrite=True,
            )
