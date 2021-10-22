"""Link a project to a Cookiecutter template."""
import contextlib
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.errors import CuttyError
from cutty.projects.generate import generate
from cutty.projects.messages import createcommitmessage
from cutty.projects.messages import linkcommitmessage
from cutty.projects.projectconfig import PROJECT_CONFIG_FILE
from cutty.projects.projectconfig import ProjectConfig
from cutty.projects.projectconfig import readcookiecutterjson
from cutty.projects.projectconfig import readprojectconfigfile
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject
from cutty.projects.template import Template
from cutty.templates.domain.bindings import Binding


class TemplateNotSpecifiedError(CuttyError):
    """The template was not specified."""


def loadprojectconfig(projectdir: pathlib.Path) -> Optional[ProjectConfig]:
    """Attempt to load the project configuration."""
    with contextlib.suppress(FileNotFoundError):
        return readprojectconfigfile(projectdir)

    with contextlib.suppress(FileNotFoundError):
        return readcookiecutterjson(projectdir)

    return None


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
    """Link project to a Cookiecutter template."""
    projectconfig = loadprojectconfig(projectdir)

    if projectconfig is not None:
        extrabindings = [*projectconfig.bindings, *extrabindings]

        if location is None:
            location = projectconfig.template

        if directory is None:
            directory = projectconfig.directory

    if location is None:
        raise TemplateNotSpecifiedError()

    template = Template.load(location, revision, directory)
    project = generate(template, extrabindings, interactive=interactive)

    repository = ProjectRepository(projectdir)

    with repository.build() as builder:
        storeproject(project, builder.path)
        commit = builder.commit(createcommitmessage(template.metadata))

    repository.link(
        commit,
        pathlib.Path(PROJECT_CONFIG_FILE),
        message=linkcommitmessage(template.metadata),
    )
