"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
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

    if directory is None:
        directory = projectconfig.directory

    repository = ProjectRepository(projectdir)
    template = Template.load(
        projectconfig.template, projectconfig.revision, projectconfig.directory
    )

    with repository.reset(template.metadata) as outputdir:
        project = generate(
            template, extrabindings=projectconfig.bindings, interactive=interactive
        )
        storeproject(project, outputdir, outputdirisproject=True)

    template = Template.load(projectconfig.template, revision, directory)

    with repository.update(template.metadata) as outputdir:
        project = generate(
            template, extrabindings=extrabindings, interactive=interactive
        )
        storeproject(project, outputdir, outputdirisproject=True)
