"""Unit tests for cutty.projects.repository."""
import dataclasses
from pathlib import Path

from cutty.packages.domain.package import Author
from cutty.packages.domain.package import Commit
from cutty.projects.config import PROJECT_CONFIG_FILE
from cutty.projects.messages import linkcommitmessage
from cutty.projects.repository import ProjectRepository
from cutty.projects.template import Template
from cutty.util.git import Repository


pytest_plugins = ["tests.fixtures.git"]


def linkproject(project: Repository, template: Template.Metadata) -> None:
    """Link a project to a project template."""
    repository = ProjectRepository(project.path)

    with repository.build() as builder:
        (builder.path / "cutty.json").touch()
        commit = builder.commit(linkcommitmessage(template))

    repository.import_(commit, paths=[Path(PROJECT_CONFIG_FILE)])


def test_linkproject_commit(
    repository: Repository, template: Template.Metadata
) -> None:
    """It creates a commit on the current branch."""
    tip = repository.head.commit

    linkproject(repository, template)

    assert [tip] == repository.head.commit.parents


def test_linkproject_commit_message(
    repository: Repository, template: Template.Metadata
) -> None:
    """It uses a commit message indicating the linkage."""
    linkproject(repository, template)

    assert "link" in repository.head.commit.message.lower()


def test_linkproject_commit_message_template(
    repository: Repository, template: Template.Metadata
) -> None:
    """It includes the template name in the commit message."""
    linkproject(repository, template)

    assert template.name in repository.head.commit.message


def test_linkproject_commit_message_revision(
    repository: Repository, template: Template.Metadata
) -> None:
    """It includes the template name in the commit message."""
    commit = Commit(
        "f4c0629d635865697b3e99b5ca581e78b2c7d976",
        "v1.0.0",
        "Release 1.0.0",
        Author("You", "you@example.com"),
    )
    template = dataclasses.replace(template, commit=commit)

    linkproject(repository, template)

    assert (
        template.commit and template.commit.revision in repository.head.commit.message
    )
