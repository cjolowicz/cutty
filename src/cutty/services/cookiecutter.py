"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.projects.generate import generate2
from cutty.projects.store import storeproject
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
) -> None:
    """Generate projects from Cookiecutter templates."""
    template = Template.load(location, checkout, directory)

    project = generate2(
        template,
        extrabindings=extrabindings,
        no_input=no_input,
        createconfigfile=False,
    )

    storeproject(
        project,
        outputdir,
        outputdirisproject=False,
        fileexists=fileexists,
    )
