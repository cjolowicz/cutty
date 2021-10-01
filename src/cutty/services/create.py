"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.projects.create import creategitrepository
from cutty.projects.generate import generate
from cutty.projects.loadtemplate import loadtemplate
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
    template = loadtemplate(location, checkout, directory)

    projectdir = generate(
        template,
        outputdir,
        extrabindings=extrabindings,
        no_input=no_input,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
        outputdirisproject=in_place,
        createconfigfile=True,
    )

    creategitrepository(projectdir, template.metadata)
