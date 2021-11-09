"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.projects.build import createproject
from cutty.projects.config import ProjectConfig
from cutty.projects.store import storeproject
from cutty.variables.domain.bindings import Binding


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
    config = ProjectConfig(location, extrabindings, checkout, directory)

    with createproject(
        config, interactive=interactive, createconfigfile=False
    ) as project:
        storeproject(
            project,
            outputdir / project.name,
            outputdirisproject=False,
            fileexists=fileexists,
        )
