"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.projects.generate import ProjectGenerator
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
    template = Template.load(location, checkout, directory)

    generator = ProjectGenerator(
        template,
        extrabindings=extrabindings,
        no_input=no_input,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
        outputdirisproject=False,
        createconfigfile=False,
    )

    generator.generate(outputdir)
