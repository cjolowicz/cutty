"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.projects.generate import generate
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject
from cutty.projects.template import Template
from cutty.templates.domain.bindings import Binding


def createproject(
    location: str,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding],
    interactive: bool,
    revision: Optional[str],
    directory: Optional[pathlib.Path],
    fileexists: FileExistsPolicy,
    in_place: bool,
) -> None:
    """Generate projects from Cookiecutter templates."""
    template = Template.load(location, revision, directory)

    project = generate(template, extrabindings=extrabindings, interactive=interactive)

    projectdir = storeproject(
        project,
        outputdir,
        outputdirisproject=in_place,
        fileexists=fileexists,
    )

    ProjectRepository.create(projectdir, template.metadata)
