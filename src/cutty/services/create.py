"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.projects.generate import generate
from cutty.projects.messages import createcommitmessage
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject
from cutty.projects.template import Template
from cutty.templates.domain.bindings import Binding


def createproject(
    location: str,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding],
    interactive: bool,
    revision: Optional[str],
    directory: Optional[pathlib.Path],
    in_place: bool,
) -> None:
    """Generate projects from Cookiecutter templates."""
    template = Template.load(location, revision, directory)

    project = generate(template, extrabindings, interactive=interactive)
    projectdir = outputdir if in_place else outputdir / project.name
    repository = ProjectRepository.create(projectdir, message="Initial commit")

    with repository.build() as builder:
        storeproject(project, builder.path)
        commit = builder.commit(message=createcommitmessage(template.metadata))

    repository.import_(commit)
