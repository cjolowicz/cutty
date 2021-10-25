"""Building projects in a repository."""
from collections.abc import Iterator
from typing import Optional

from cutty.compat.contextlib import contextmanager
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
    with createproject2(
        config, interactive=interactive, createconfigfile=createconfigfile
    ) as project:
        return project


@contextmanager
def createproject2(
    config: ProjectConfig, *, interactive: bool, createconfigfile: bool = True
) -> Iterator[Project]:
    """Create the project."""
    with Template.load(config.template, config.revision, config.directory) as template:
        yield generate(
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
