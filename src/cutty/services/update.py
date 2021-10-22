"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from cutty.projects.generate import generate
from cutty.projects.messages import createcommitmessage
from cutty.projects.messages import updatecommitmessage
from cutty.projects.projectconfig import ProjectConfig
from cutty.projects.projectconfig import readprojectconfigfile
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject
from cutty.projects.template import Template
from cutty.templates.domain.bindings import Binding


def _create(
    repository: ProjectRepository, projectconfig: ProjectConfig, interactive: bool
) -> str:
    """Create the project and return the commit ID."""
    template = Template.load(
        projectconfig.template, projectconfig.revision, projectconfig.directory
    )
    project = generate(template, projectconfig.bindings, interactive=interactive)

    with repository.build() as builder:
        storeproject(project, builder.path)
        return builder.commit(createcommitmessage(template.metadata))


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

    repository = ProjectRepository(projectdir)

    commit = _create(repository, projectconfig, interactive)

    projectconfig2 = ProjectConfig(
        projectconfig.template, extrabindings, revision, directory
    )

    template = Template.load(
        projectconfig2.template, projectconfig2.revision, projectconfig2.directory
    )
    project = generate(template, projectconfig2.bindings, interactive=interactive)

    with repository.build(parent=commit) as builder:
        storeproject(project, builder.path)
        commit2 = builder.commit(updatecommitmessage(template.metadata))

    if commit2 != commit:
        repository.import_(commit2)
