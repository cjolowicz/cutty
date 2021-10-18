"""Unit tests for cutty.projects.repository."""
import dataclasses

import pytest

from cutty.projects.repository import createcommitmessage
from cutty.projects.repository import linkcommitmessage
from cutty.projects.repository import ProjectRepository
from cutty.projects.template import Template
from cutty.util.git import Repository


pytest_plugins = ["tests.fixtures.git"]


def linkproject(project: Repository, template: Template.Metadata) -> None:
    """Link a project to a project template."""
    repository = ProjectRepository(project.path)

    with repository.build(parent=repository.root) as builder:
        (builder.path / "cutty.json").touch()
        commit2 = builder.commit(createcommitmessage(template))

    repository.updateconfig(message=linkcommitmessage(template), commit=commit2)


@pytest.fixture
def project(repository: Repository) -> Repository:
    """Fixture for a project repository."""
    return repository


def test_linkproject_commit(project: Repository, template: Template.Metadata) -> None:
    """It creates a commit on the current branch."""
    tip = project.head.commit

    linkproject(project, template)

    assert [tip] == project.head.commit.parents


def test_linkproject_commit_message(
    project: Repository, template: Template.Metadata
) -> None:
    """It uses a commit message indicating the linkage."""
    linkproject(project, template)

    assert "link" in project.head.commit.message.lower()


def test_linkproject_commit_message_template(
    project: Repository, template: Template.Metadata
) -> None:
    """It includes the template name in the commit message."""
    linkproject(project, template)

    assert template.name in project.head.commit.message


def test_linkproject_commit_message_revision(
    project: Repository, template: Template.Metadata
) -> None:
    """It includes the template name in the commit message."""
    template = dataclasses.replace(template, revision="1.0.0")

    linkproject(project, template)

    assert template.revision in project.head.commit.message
