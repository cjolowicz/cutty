"""Building projects in a repository."""
from typing import Optional

from cutty.projects.generate import generate
from cutty.projects.messages import MessageBuilder
from cutty.projects.project import Project
from cutty.projects.projectconfig import ProjectConfig
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject
from cutty.projects.template import Template


def createproject(config: ProjectConfig, *, interactive: bool) -> Project:
    """Create the project."""
    template = Template.load(config.template, config.revision, config.directory)

    return generate(template, config.bindings, interactive=interactive)


def buildproject(
    repository: ProjectRepository,
    config: ProjectConfig,
    *,
    interactive: bool,
    parent: Optional[str] = None,
    commitmessage: MessageBuilder,
) -> str:
    """Build the project, returning the commit ID."""
    project = createproject(config, interactive=interactive)

    with repository.build(parent=parent) as builder:
        storeproject(project, builder.path)
        return builder.commit(commitmessage(project.template))
