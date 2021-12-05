"""Building projects in a repository."""
import datetime
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.packages.domain.package import Author
from cutty.projects.config import ProjectConfig
from cutty.projects.generate import generate
from cutty.projects.messages import MessageBuilder
from cutty.projects.project import Project
from cutty.projects.repository import ProjectRepository
from cutty.projects.store import storeproject
from cutty.projects.template import TemplateProvider
from cutty.variables.domain.bindings import Binding


@contextmanager
def createproject(
    config: ProjectConfig,
    *,
    interactive: bool,
    createconfigfile: bool = True,
    userbindings: Sequence[Binding] = (),
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
            userbindings=userbindings,
        )


def commitproject(
    repository: ProjectRepository,
    project: Project,
    *,
    parent: Optional[str] = None,
    commitmessage: Optional[MessageBuilder] = None,
) -> str:
    """Build the project, returning the commit ID."""
    with repository.build(parent=parent) as builder:
        storeproject(project, builder.path)

        author: Optional[Author] = None
        date: Optional[datetime.datetime] = None

        if commitmessage is not None:
            message = commitmessage(project.template)
        elif project.template.commit:
            message = project.template.commit.message
            author = project.template.commit.author
            date = project.template.commit.date
        else:  # pragma: no cover
            # The `commitmessage` is only None when importing, and imports are only
            # possible when there's a `template.commit`. So this should be unreachable.
            message = f"Import {project.template.name}"

        return builder.commit(message, author=author, date=date)


def buildproject(
    repository: ProjectRepository,
    config: ProjectConfig,
    *,
    userbindings: Sequence[Binding] = (),
    interactive: bool,
    parent: Optional[str] = None,
    commitmessage: Optional[MessageBuilder] = None,
) -> str:
    """Build the project, returning the commit ID."""
    with createproject(
        config, userbindings=userbindings, interactive=interactive
    ) as project:
        return commitproject(
            repository, project, parent=parent, commitmessage=commitmessage
        )


def buildparentproject(
    repository: ProjectRepository,
    config: ProjectConfig,
    *,
    userbindings: Sequence[Binding] = (),
    revision: Optional[str],
    interactive: bool,
) -> Optional[str]:
    """Build the project for the parent revision."""
    provider = TemplateProvider.create()
    templates = provider.provide(config.template, config.directory)

    if parentrevision := templates.getparentrevision(revision):
        with templates.get(parentrevision) as template:
            project = generate(
                template,
                config.bindings,
                userbindings=userbindings,
                interactive=interactive,
            )
            return commitproject(repository, project)

    return None
