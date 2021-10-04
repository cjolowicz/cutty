"""Unit tests for cutty.services.link."""
import dataclasses

import pytest

from cutty.projects.repository import GenerateProject
from cutty.projects.repository import LATEST_BRANCH
from cutty.projects.repository import ProjectRepository
from cutty.projects.repository import UPDATE_BRANCH
from cutty.projects.template import Template
from cutty.util.git import Repository
from tests.util.git import updatefile


pytest_plugins = ["tests.fixtures.git"]


def linkproject(
    project: Repository,
    generateproject: GenerateProject,
    template: Template.Metadata,
) -> None:
    """Link a project to a project template."""
    repository = ProjectRepository(project.path)
    with repository.link(template) as projectdir:
        generateproject(projectdir)


@pytest.fixture
def project(repository: Repository) -> Repository:
    """Fixture for a project repository."""
    return repository


def test_linkproject_commit(
    project: Repository, generateproject: GenerateProject, template: Template.Metadata
) -> None:
    """It creates a commit on the current branch."""
    tip = project.head.commit

    linkproject(project, generateproject, template)

    assert [tip] == project.head.commit.parents


def test_linkproject_commit_message(
    project: Repository, generateproject: GenerateProject, template: Template.Metadata
) -> None:
    """It uses a commit message indicating the linkage."""
    linkproject(project, generateproject, template)

    assert "link" in project.head.commit.message.lower()


def test_linkproject_commit_message_template(
    project: Repository,
    generateproject: GenerateProject,
    template: Template.Metadata,
) -> None:
    """It includes the template name in the commit message."""
    linkproject(project, generateproject, template)

    assert template.name in project.head.commit.message


def test_linkproject_commit_message_revision(
    project: Repository, generateproject: GenerateProject, template: Template.Metadata
) -> None:
    """It includes the template name in the commit message."""
    template = dataclasses.replace(template, revision="1.0.0")

    linkproject(project, generateproject, template)

    assert template.revision in project.head.commit.message


def test_linkproject_latest_branch(
    project: Repository, generateproject: GenerateProject, template: Template.Metadata
) -> None:
    """It creates the latest branch."""
    updatefile(project.path / "initial")

    linkproject(project, generateproject, template)

    assert LATEST_BRANCH in project.heads


def test_linkproject_latest_branch_commit_message(
    project: Repository, generateproject: GenerateProject, template: Template.Metadata
) -> None:
    """It uses a commit message indicating an initial import."""
    updatefile(project.path / "initial")

    linkproject(project, generateproject, template)

    assert "initial" in project.heads[LATEST_BRANCH].message.lower()


def test_linkproject_latest_branch_commit_message_update(
    project: Repository, generateproject: GenerateProject, template: Template.Metadata
) -> None:
    """It uses a commit message indicating an update if the branch exists."""
    project.heads.create(LATEST_BRANCH)

    updatefile(project.path / "initial")

    linkproject(project, generateproject, template)

    assert "update" in project.heads[LATEST_BRANCH].message.lower()


def test_linkproject_update_branch(
    project: Repository, generateproject: GenerateProject, template: Template.Metadata
) -> None:
    """It creates the update branch."""
    updatefile(project.path / "initial")

    linkproject(project, generateproject, template)

    assert UPDATE_BRANCH in project.heads
