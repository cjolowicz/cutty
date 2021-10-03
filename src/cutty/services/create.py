"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.projects.generate import generate
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
    fileexists: FileExistsPolicy,
    in_place: bool,
) -> None:
    """Generate projects from Cookiecutter templates."""
    template = Template.load(location, checkout, directory)

    projectdir = generate(
        template,
        outputdir,
        extrabindings=extrabindings,
        no_input=no_input,
        fileexists=fileexists,
        outputdirisproject=in_place,
        createconfigfile=True,
    )

    ProjectRepository.create(projectdir, template.metadata)
