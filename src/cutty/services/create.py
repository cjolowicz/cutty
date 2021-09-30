"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.projects.create import creategitrepository
from cutty.services.generate import (  # noqa: F401
    EmptyTemplateError as EmptyTemplateError,
)
from cutty.services.generate import generate
from cutty.services.loadtemplate import loadtemplate2
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
    template = loadtemplate2(location, checkout, directory)

    projectdir = generate(
        location,
        template.repository,
        outputdir,
        extrabindings=extrabindings,
        no_input=no_input,
        checkout=checkout,
        directory=directory,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
        outputdirisproject=in_place,
        createconfigfile=True,
    )

    creategitrepository(projectdir, template.repository)
