"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.projects.generate import fileexistspolicy
from cutty.projects.generate import generate
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
) -> None:
    """Generate projects from Cookiecutter templates."""
    fileexists = fileexistspolicy(overwrite_if_exists, skip_if_file_exists)
    createproject2(
        location,
        outputdir,
        extrabindings=extrabindings,
        no_input=no_input,
        checkout=checkout,
        directory=directory,
        fileexists=fileexists,
    )


def createproject2(
    location: str,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding],
    no_input: bool,
    checkout: Optional[str],
    directory: Optional[pathlib.PurePosixPath],
    fileexists: FileExistsPolicy,
) -> None:
    """Generate projects from Cookiecutter templates."""
    template = Template.load(location, checkout, directory)

    generate(
        template,
        outputdir,
        extrabindings=extrabindings,
        no_input=no_input,
        fileexists=fileexists,
        outputdirisproject=False,
        createconfigfile=False,
    )
