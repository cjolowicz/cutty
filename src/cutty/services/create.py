"""Create a project from a template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.projects.build import commitproject
from cutty.projects.build import createproject
from cutty.projects.messages import createcommitmessage
from cutty.projects.projectconfig import ProjectConfig
from cutty.projects.repository import ProjectRepository
from cutty.templates.domain.bindings import Binding


def create(
    location: str,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding],
    interactive: bool,
    revision: Optional[str],
    directory: Optional[pathlib.Path],
    in_place: bool,
) -> None:
    """Generate projects from templates."""
    config = ProjectConfig(location, extrabindings, revision, directory)

    project = createproject(config, interactive=interactive)
    projectdir = outputdir if in_place else outputdir / project.name
    repository = ProjectRepository.create(projectdir, message="Initial commit")

    commit = commitproject(repository, project, commitmessage=createcommitmessage)

    repository.import_(commit)
