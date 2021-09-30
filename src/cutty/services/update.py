"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from pathlib import PurePosixPath
from typing import Optional

from cutty.projects.update import updateproject2
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.generate import generate
from cutty.services.loadtemplate import loadtemplate
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.templates.domain.bindings import Binding


def update(
    projectdir: Path,
    *,
    extrabindings: Sequence[Binding],
    no_input: bool,
    checkout: Optional[str],
    directory: Optional[PurePosixPath],
) -> None:
    """Update a project with changes from its Cookiecutter template."""
    projectconfig = readprojectconfigfile(projectdir)
    extrabindings = list(projectconfig.bindings) + list(extrabindings)

    if directory is None:
        directory = projectconfig.directory

    template = loadtemplate(projectconfig.template, checkout, directory)

    def createproject(outputdir: Path) -> Template:
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
        return template.repository

    updateproject2(projectdir, createproject, template)
