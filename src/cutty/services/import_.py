"""Import changes from templates into projects."""
from pathlib import Path
from typing import Optional

from cutty.projects.build import buildproject
from cutty.projects.config import ProjectConfig
from cutty.projects.config import readprojectconfigfile
from cutty.projects.messages import updatecommitmessage
from cutty.projects.repository import ProjectRepository


def import_(projectdir: Path, *, revision: Optional[str]) -> None:
    """Import changes from a template into a project."""
    config1 = readprojectconfigfile(projectdir)

    config2 = ProjectConfig(
        config1.template,
        config1.bindings,
        revision,
        config1.directory,
    )

    repository = ProjectRepository(projectdir)

    parent = buildproject(
        repository,
        config1,
        interactive=True,
        commitmessage=updatecommitmessage,
    )

    commit = buildproject(
        repository,
        config2,
        interactive=True,
        commitmessage=updatecommitmessage,
        parent=parent,
    )

    if commit != parent:
        repository.import_(commit)
