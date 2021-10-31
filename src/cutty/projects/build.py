"""Building projects in a repository."""
from collections.abc import Iterator
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.projects.config import ProjectConfig
from cutty.projects.generate import generate
from cutty.projects.messages import MessageBuilder
from cutty.projects.project import Project
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject
from cutty.projects.template import TemplateProvider


@contextmanager
def createproject(
    config: ProjectConfig, *, interactive: bool, createconfigfile: bool = True
) -> Iterator[Project]:
    """Create the project."""
    provider = TemplateProvider.create()
    templates = provider.provide(config.template, config.directory)

    with templates.get(config.revision) as template:
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
    with createproject(config, interactive=interactive) as project:
        return commitproject(
            repository, project, parent=parent, commitmessage=commitmessage
        )


def buildparentproject(
    repository: ProjectRepository,
    config: ProjectConfig,
    *,
    revision: Optional[str],
    interactive: bool,
    commitmessage: MessageBuilder,
) -> Optional[str]:
    """Build the project for the parent revision."""
    provider = TemplateProvider.create()
    templates = provider.provide(config.template, config.directory)

    if parentrevision := templates.getparentrevision(revision):
        with templates.get(parentrevision) as template:
            project = generate(template, config.bindings, interactive=interactive)
            return commitproject(repository, project, commitmessage=commitmessage)

    return None
