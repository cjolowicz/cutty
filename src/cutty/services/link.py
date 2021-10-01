"""Link a project to a Cookiecutter template."""
import contextlib
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.errors import CuttyError
from cutty.projects.generate import generate
from cutty.projects.repository import ProjectRepository
from cutty.projects.template import Template
from cutty.templates.adapters.cookiecutter.projectconfig import readcookiecutterjson
from cutty.templates.domain.bindings import Binding


class TemplateNotSpecifiedError(CuttyError):
    """The template was not specified."""


def link(
    location: Optional[str],
    projectdir: pathlib.Path,
    /,
    *,
    extrabindings: Sequence[Binding],
    no_input: bool,
    checkout: Optional[str],
    directory: Optional[pathlib.PurePosixPath],
) -> None:
    """Link project to a Cookiecutter template."""
    with contextlib.suppress(FileNotFoundError):
        projectconfig = readcookiecutterjson(projectdir)
        extrabindings = list(projectconfig.bindings) + list(extrabindings)

        if location is None:
            location = projectconfig.template

    if location is None:
        raise TemplateNotSpecifiedError()

    template = Template.load(location, checkout, directory)

    def generateproject(outputdir: pathlib.Path) -> None:
        generate(
            template,
            outputdir,
            extrabindings=extrabindings,
            no_input=no_input,
            overwrite_if_exists=False,
            skip_if_file_exists=False,
            outputdirisproject=True,
            createconfigfile=True,
        )

    project = ProjectRepository(projectdir)
    project.link(generateproject, template.metadata)
