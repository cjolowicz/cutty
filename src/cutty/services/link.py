"""Link a project to a Cookiecutter template."""
import contextlib
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.errors import CuttyError
from cutty.projects.generate import generate
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


def createprojectconfig(
    projectdir: pathlib.Path,
    location: Optional[str],
    bindings: Sequence[Binding],
    revision: Optional[str],
    directory: Optional[pathlib.Path],
) -> ProjectConfig:
    """Assemble project configuration from parameters and the existing project."""
    projectconfig = loadprojectconfig(projectdir)

    if projectconfig is not None:
        bindings = [*projectconfig.bindings, *bindings]

        if location is None:
            location = projectconfig.template

        if directory is None:
            directory = projectconfig.directory

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
    """Link project to a Cookiecutter template."""
    projectconfig = createprojectconfig(
        projectdir, location, extrabindings, revision, directory
    )

    template = Template.load(
        projectconfig.template, projectconfig.revision, projectconfig.directory
    )
    project = generate(template, projectconfig.bindings, interactive=interactive)

    repository = ProjectRepository(projectdir)

    with repository.build() as builder:
        storeproject(project, builder.path)
        commit = builder.commit(linkcommitmessage(template.metadata))

    repository.import2(
        commit,
        paths=[pathlib.Path(PROJECT_CONFIG_FILE)],
        message=linkcommitmessage(template.metadata),
    )
