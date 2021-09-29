"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.projects.create import creategitrepository
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.generate import (  # noqa: F401
    EmptyTemplateError as EmptyTemplateError,
)
from cutty.services.generate import generate
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
    projectdir, template = create(
        location,
        outputdir,
        extrabindings=extrabindings,
        no_input=no_input,
        checkout=checkout,
        directory=directory,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
        outputdirisproject=in_place,
    )

    creategitrepository(projectdir, template)


def create(
    location: str,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[pathlib.PurePosixPath] = None,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
    outputdirisproject: bool = False,
    createrepository: bool = True,
    createconfigfile: bool = True,
) -> tuple[pathlib.Path, Template]:
    """Generate a project from a Cookiecutter template."""
    return generate(
        location,
        outputdir,
        extrabindings=extrabindings,
        no_input=no_input,
        checkout=checkout,
        directory=directory,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
        outputdirisproject=outputdirisproject,
        createrepository=createrepository,
        createconfigfile=createconfigfile,
    )
