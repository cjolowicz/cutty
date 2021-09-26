"""Unit tests for cutty.services.link."""
from pathlib import Path

import pytest

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path as VirtualPath
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.link import CreateProject
from cutty.services.link import linkproject
from cutty.util.git import Repository


pytest_plugins = ["tests.fixtures.git"]


@pytest.fixture
def project(repository: Repository) -> Repository:
    """Fixture for a project repository."""
    return repository


@pytest.fixture
def template() -> Template:
    """Fixture for a `Template` instance."""
    templatepath = VirtualPath(filesystem=DictFilesystem({}))
    return Template("template", templatepath, None)


@pytest.fixture
def createproject(template: Template) -> CreateProject:
    """Fixture for a `createproject` function."""

    def _(project: Path) -> Template:
        (project / "cutty.json").touch()
        return template

    return _


def test_linkproject_commit(project: Repository, createproject: CreateProject) -> None:
    """It creates a commit on the current branch."""
    tip = project.head.commit

    linkproject(project, createproject)

    assert [tip] == project.head.commit.parents


def test_linkproject_commit_message(
    project: Repository, createproject: CreateProject
) -> None:
    """It uses a commit message indicating the linkage."""
    linkproject(project, createproject)

    assert "link" in project.head.commit.message.lower()


def test_linkproject_commit_message_template(
    project: Repository, createproject: CreateProject, template: Template
) -> None:
    """It includes the template name in the commit message."""
    linkproject(project, createproject)

    assert template.name in project.head.commit.message
