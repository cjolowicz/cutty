"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from pathlib import PurePosixPath
from typing import Optional

from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.projects.generate import generate
from cutty.projects.repository import ProjectRepository
from cutty.projects.template import Template
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

    template = Template.load(projectconfig.template, checkout, directory)

    def generateproject(outputdir: Path) -> None:
        generate(
            template,
            outputdir,
            extrabindings=extrabindings,
            no_input=no_input,
            fileexists=FileExistsPolicy.RAISE,
            outputdirisproject=True,
            createconfigfile=True,
        )

    project = ProjectRepository(projectdir)
    project.update(generateproject, template.metadata)
