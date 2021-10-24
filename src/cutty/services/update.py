"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from cutty.projects.build import buildproject
from cutty.projects.messages import MessageBuilder
from cutty.projects.messages import updatecommitmessage
from cutty.projects.projectconfig import ProjectConfig
from cutty.projects.projectconfig import readprojectconfigfile
from cutty.projects.repository import ProjectRepository
from cutty.templates.domain.bindings import Binding


def _create(
    repository: ProjectRepository,
    config: ProjectConfig,
    *,
    interactive: bool,
    parent: Optional[str] = None,
    commitmessage: MessageBuilder,
) -> str:
    """Create the project and return the commit ID."""
    return buildproject(
        repository,
        config,
        interactive=interactive,
        parent=parent,
        commitmessage=commitmessage,
    )


def update(
    projectdir: Path,
    *,
    extrabindings: Sequence[Binding],
    interactive: bool,
    revision: Optional[str],
    directory: Optional[Path],
) -> None:
    """Update a project with changes from its Cookiecutter template."""
    config1 = readprojectconfigfile(projectdir)

    config2 = ProjectConfig(
        config1.template,
        [*config1.bindings, *extrabindings],
        revision,
        config1.directory if directory is None else directory,
    )

    repository = ProjectRepository(projectdir)

    parent = _create(
        repository,
        config1,
        interactive=interactive,
        commitmessage=updatecommitmessage,
    )

    commit = _create(
        repository,
        config2,
        interactive=interactive,
        commitmessage=updatecommitmessage,
        parent=parent,
    )

    if commit != parent:
        repository.import_(commit)
