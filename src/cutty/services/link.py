"""Link a project to a Cookiecutter template."""
import contextlib
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.errors import CuttyError
from cutty.projects.generate import generate
from cutty.projects.projectconfig import readcookiecutterjson
from cutty.projects.repository import createcommitmessage
from cutty.projects.repository import linkcommitmessage
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject2
from cutty.projects.template import Template
from cutty.templates.domain.bindings import Binding


class TemplateNotSpecifiedError(CuttyError):
    """The template was not specified."""


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
    with contextlib.suppress(FileNotFoundError):
        projectconfig = readcookiecutterjson(projectdir)
        extrabindings = [*projectconfig.bindings, *extrabindings]

        if location is None:
            location = projectconfig.template

    if location is None:
        raise TemplateNotSpecifiedError()

    template = Template.load(location, revision, directory)
    project = generate(template, extrabindings, interactive=interactive)

    repository = ProjectRepository(projectdir)

    with repository.build(parent=repository.root) as builder:
        outputdir = builder.path
        projectdir = outputdir
        storeproject2(project, projectdir)
        commit2 = builder.commit(createcommitmessage(template.metadata))

    repository.link(message=linkcommitmessage(template.metadata), commit=commit2)
