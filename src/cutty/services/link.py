"""Link a project to a template."""
import contextlib
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.errors import CuttyError
from cutty.projects.build import buildproject
from cutty.projects.config import PROJECT_CONFIG_FILE
from cutty.projects.config import ProjectConfig
from cutty.projects.config import readcookiecutterjson
from cutty.projects.config import readprojectconfigfile
from cutty.projects.messages import linkcommitmessage
from cutty.projects.repository import ProjectRepository
from cutty.variables.domain.bindings import Binding


class TemplateNotSpecifiedError(CuttyError):
    """The template was not specified."""


def loadprojectconfig(projectdir: pathlib.Path) -> Optional[ProjectConfig]:
    """Attempt to load the project configuration."""
    with contextlib.suppress(FileNotFoundError):
        return readprojectconfigfile(projectdir)

    with contextlib.suppress(FileNotFoundError):
        return readcookiecutterjson(projectdir)

    return None


def createprojectconfig(
    projectdir: pathlib.Path,
    location: Optional[str],
    bindings: Sequence[Binding],
    revision: Optional[str],
    directory: Optional[pathlib.Path],
) -> ProjectConfig:
    """Assemble project configuration from parameters and the existing project."""
    config = loadprojectconfig(projectdir)

    if config is not None:
        bindings = [*config.bindings, *bindings]

        if location is None:
            location = config.template

        if directory is None:
            directory = config.directory

    if location is None:
        raise TemplateNotSpecifiedError()

    return ProjectConfig(location, bindings, revision, directory)


def link(
    location: Optional[str],
    projectdir: pathlib.Path,
    /,
    *,
    extrabindings: Sequence[Binding],
    interactive: bool,
    revision: Optional[str],
    directory: Optional[pathlib.Path],
) -> None:
    """Link project to a template."""
    config = createprojectconfig(
        projectdir, location, extrabindings, revision, directory
    )

    repository = ProjectRepository(projectdir)

    commit = buildproject(
        repository,
        config,
        interactive=interactive,
        commitmessage=linkcommitmessage,
    )

    repository.import_(commit, paths=[pathlib.Path(PROJECT_CONFIG_FILE)])
