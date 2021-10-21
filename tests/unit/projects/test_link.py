"""Unit tests for cutty.projects.repository."""
import dataclasses

from cutty.projects.messages import createcommitmessage
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
        commit = builder.commit(createcommitmessage(template))

    repository.link2(commit, message=linkcommitmessage(template))


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
    template = dataclasses.replace(template, revision="1.0.0")

    linkproject(repository, template)

    assert template.revision in repository.head.commit.message
