"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.projects.generate import generate
from cutty.projects.store import storeproject
from cutty.projects.template import Template
from cutty.templates.domain.bindings import Binding


def createproject(
    location: str,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding],
    interactive: bool,
    checkout: Optional[str],
    directory: Optional[pathlib.PurePosixPath],
    fileexists: FileExistsPolicy,
) -> None:
    """Generate projects from Cookiecutter templates."""
    createproject2(
        location,
        outputdir,
        extrabindings=extrabindings,
        interactive=interactive,
        checkout=checkout,
        directory=pathlib.Path(directory) if directory is not None else None,
        fileexists=fileexists,
    )


def createproject2(
    location: str,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding],
    interactive: bool,
    checkout: Optional[str],
    directory: Optional[pathlib.Path],
    fileexists: FileExistsPolicy,
) -> None:
    """Generate projects from Cookiecutter templates."""
    template = Template.load(
        location,
        checkout,
        pathlib.PurePosixPath(directory) if directory is not None else None,
    )

    project = generate(
        template,
        extrabindings=extrabindings,
        interactive=interactive,
        createconfigfile=False,
    )

    storeproject(
        project,
        outputdir,
        outputdirisproject=False,
        fileexists=fileexists,
    )
