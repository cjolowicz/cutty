"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from pathlib import PurePosixPath
from typing import Optional

from cutty.projects.generate import generate
from cutty.projects.projectconfig import readprojectconfigfile
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject
from cutty.projects.template import Template
from cutty.templates.domain.bindings import Binding


def update(
    projectdir: Path,
    *,
    extrabindings: Sequence[Binding],
    interactive: bool,
    revision: Optional[str],
    directory: Optional[Path],
) -> None:
    """Update a project with changes from its Cookiecutter template."""
    projectconfig = readprojectconfigfile(projectdir)
    extrabindings = list(projectconfig.bindings) + list(extrabindings)

    directory2 = PurePosixPath(directory) if directory is not None else None
    if directory is None:
        directory2 = projectconfig.directory

    template = Template.load(projectconfig.template, revision, directory2)
    repository = ProjectRepository(projectdir)

    with repository.update(template.metadata) as outputdir:
        project = generate(
            template, extrabindings=extrabindings, interactive=interactive
        )
        storeproject(project, outputdir, outputdirisproject=True)
