"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.projects.generate import generate
from cutty.projects.store import storeproject
from cutty.projects.template import Template
from cutty.templates.domain.bindings import Binding


def create(
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
    template = Template.load(location, checkout, directory)

    project = generate(
        template, extrabindings, interactive=interactive, createconfigfile=False
    )

    storeproject(
        project,
        outputdir / project.name,
        outputdirisproject=False,
        fileexists=fileexists,
    )
