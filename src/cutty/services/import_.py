"""Import changes from templates into projects."""
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from cutty.projects.build import buildparentproject
from cutty.projects.build import buildproject
from cutty.projects.config import ProjectConfig
from cutty.projects.config import readprojectconfigfile
from cutty.projects.messages import importcommitmessage
from cutty.projects.repository import ProjectRepository
from cutty.variables.domain.bindings import Binding


def import_(
    projectdir: Path,
    *,
    revision: Optional[str],
    extrabindings: Sequence[Binding],
    interactive: bool,
    directory: Optional[Path]
) -> None:
    """Import changes from a template into a project."""
    config1 = readprojectconfigfile(projectdir)

    config2 = ProjectConfig(
        config1.template,
        [*config1.bindings, *extrabindings],
        revision,
        config1.directory if directory is None else directory,
    )

    repository = ProjectRepository(projectdir)

    parent = buildparentproject(
        repository,
        config1,
        revision=revision,
        interactive=interactive,
        commitmessage=importcommitmessage,
    )

    commit = buildproject(
        repository,
        config2,
        interactive=interactive,
        commitmessage=importcommitmessage,
        parent=parent,
    )

    # If `commit` and `parent` are identical then so is the template revision
    # stored in their cutty.json. But for the version control systems we
    # support, commits never have the same hash as their parents.
    assert commit != parent  # noqa: S101

    repository.import_(commit)
