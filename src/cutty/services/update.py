"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from cutty.projects.generate import generate
from cutty.projects.projectconfig import readprojectconfigfile
from cutty.projects.repository import createcommitmessage
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
    extrabindings = [*projectconfig.bindings, *extrabindings]

    if directory is None:
        directory = projectconfig.directory

    repository = ProjectRepository(projectdir)
    template = Template.load(
        projectconfig.template, projectconfig.revision, projectconfig.directory
    )
    project = generate(template, projectconfig.bindings, interactive=interactive)

    with repository.build(repository.root) as builder:
        builder.message = createcommitmessage(template.metadata)
        storeproject(project, builder.path, outputdirisproject=True)
        builder.commit2()

    template = Template.load(projectconfig.template, revision, directory)
    project = generate(template, extrabindings, interactive=interactive)

    with repository.update(template.metadata, parent=builder.commit) as outputdir:
        storeproject(project, outputdir, outputdirisproject=True)
