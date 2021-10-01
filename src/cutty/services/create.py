"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.projects.generate import fileexistspolicy
from cutty.projects.generate import generate2
from cutty.projects.repository import ProjectRepository
from cutty.projects.template import Template
from cutty.templates.domain.bindings import Binding


def createproject(
    location: str,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding],
    no_input: bool,
    checkout: Optional[str],
    directory: Optional[pathlib.PurePosixPath],
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
    in_place: bool,
) -> None:
    """Generate projects from Cookiecutter templates."""
    template = Template.load(location, checkout, directory)

    fileexists = fileexistspolicy(overwrite_if_exists, skip_if_file_exists)
    projectdir = generate2(
        template,
        outputdir,
        extrabindings=extrabindings,
        no_input=no_input,
        fileexists=fileexists,
        outputdirisproject=in_place,
        createconfigfile=True,
    )

    ProjectRepository.create(projectdir, template.metadata)
