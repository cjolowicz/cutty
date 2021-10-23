"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from cutty.projects.generate import generate
from cutty.projects.messages import updatecommitmessage
from cutty.projects.projectconfig import ProjectConfig
from cutty.projects.projectconfig import readprojectconfigfile
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject
from cutty.projects.template import Template
from cutty.templates.domain.bindings import Binding


def _create(
    repository: ProjectRepository,
    projectconfig: ProjectConfig,
    interactive: bool,
    parent: Optional[str] = None,
) -> str:
    """Create the project and return the commit ID."""
    template = Template.load(
        projectconfig.template, projectconfig.revision, projectconfig.directory
    )
    project = generate(template, projectconfig.bindings, interactive=interactive)

    with repository.build(parent=parent) as builder:
        storeproject(project, builder.path)
        return builder.commit(updatecommitmessage(template.metadata))


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
    extrabindings = [*projectconfig.bindings, *extrabindings]

    if directory is None:
        directory = projectconfig.directory

    projectconfig2 = ProjectConfig(
        projectconfig.template, extrabindings, revision, directory
    )

    repository = ProjectRepository(projectdir)

    parent = _create(repository, projectconfig, interactive)
    commit2 = _create(repository, projectconfig2, interactive, parent=parent)

    if commit2 != parent:
        repository.import_(commit2)
