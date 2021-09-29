"""Link a project to a Cookiecutter template."""
import contextlib
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.errors import CuttyError
from cutty.projects.link import linkproject
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.generate import generate
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
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[pathlib.PurePosixPath] = None,
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

    def createproject(outputdir: pathlib.Path) -> Template:
        assert template is not None  # noqa: S101

        _, template2 = generate(
            template,
            outputdir,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )
        return template2

    linkproject(project, createproject)
