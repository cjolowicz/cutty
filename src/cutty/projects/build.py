"""Building projects in a repository."""
from typing import Optional

from cutty.projects.generate import generate
from cutty.projects.messages import MessageBuilder
from cutty.projects.project import Project
from cutty.projects.projectconfig import ProjectConfig
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject
from cutty.projects.template import Template


def createproject(
    config: ProjectConfig, *, interactive: bool, createconfigfile: bool = True
) -> Project:
    """Create the project."""
    with Template.load2(config.template, config.revision, config.directory) as template:
        pass

    return generate(
        template,
        config.bindings,
        interactive=interactive,
        createconfigfile=createconfigfile,
    )


def commitproject(
    repository: ProjectRepository,
    project: Project,
    *,
    parent: Optional[str] = None,
    commitmessage: MessageBuilder,
) -> str:
    """Build the project, returning the commit ID."""
    with repository.build(parent=parent) as builder:
        storeproject(project, builder.path)

        return builder.commit(commitmessage(project.template))


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

    return commitproject(
        repository, project, parent=parent, commitmessage=commitmessage
    )
