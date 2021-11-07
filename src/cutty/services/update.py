"""Update a project with changes from its template."""
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from cutty.projects.build import buildproject
from cutty.projects.config import ProjectConfig
from cutty.projects.config import readprojectconfigfile
from cutty.projects.messages import updatecommitmessage
from cutty.projects.repository import ProjectRepository
from cutty.variables.domain.bindings import Binding


def update(
    projectdir: Path,
    *,
    extrabindings: Sequence[Binding],
    interactive: bool,
    revision: Optional[str],
    directory: Optional[Path],
) -> None:
    """Update a project with changes from its template."""
    config1 = readprojectconfigfile(projectdir)

    config2 = ProjectConfig(
        config1.template,
        [*config1.bindings, *extrabindings],
        revision,
        config1.directory if directory is None else directory,
    )

    repository = ProjectRepository(projectdir)

    parent = buildproject(
        repository,
        config1,
        interactive=interactive,
        commitmessage=updatecommitmessage,
    )

    commit = buildproject(
        repository,
        config2,
        interactive=interactive,
        commitmessage=updatecommitmessage,
        parent=parent,
    )

    if commit != parent:
        repository.import_(commit)
