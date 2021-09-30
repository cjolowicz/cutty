"""Link a project to a Cookiecutter template."""
import contextlib
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.errors import CuttyError
from cutty.projects.link import linkproject
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.generate import generate
from cutty.services.loadtemplate import loadtemplate2
from cutty.templates.adapters.cookiecutter.projectconfig import readcookiecutterjson
from cutty.templates.domain.bindings import Binding
from cutty.util.git import Repository


class TemplateNotSpecifiedError(CuttyError):
    """The template was not specified."""


def link(
    template: Optional[str],
    projectdir: pathlib.Path,
    /,
    *,
    extrabindings: Sequence[Binding],
    no_input: bool,
    checkout: Optional[str],
    directory: Optional[pathlib.PurePosixPath],
) -> None:
    """Link project to a Cookiecutter template."""
    project = Repository.open(projectdir)

    with contextlib.suppress(FileNotFoundError):
        projectconfig = readcookiecutterjson(project.path)
        extrabindings = list(projectconfig.bindings) + list(extrabindings)

        if template is None:
            template = projectconfig.template

    if template is None:
        raise TemplateNotSpecifiedError()

    template2 = loadtemplate2(template, checkout, directory)

    def createproject(outputdir: pathlib.Path) -> Template:
        assert template is not None  # noqa: S101

        generate(
            template,
            template2.repository,
            outputdir,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
            overwrite_if_exists=False,
            skip_if_file_exists=False,
            outputdirisproject=True,
            createconfigfile=True,
        )
        return template2.repository

    linkproject(project, createproject)
