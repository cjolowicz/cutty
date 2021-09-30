"""Unit tests for cutty.services.link."""
import dataclasses
from pathlib import Path

import pytest

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path as VirtualPath
from cutty.projects.common import CreateProject
from cutty.projects.common import LATEST_BRANCH
from cutty.projects.common import UPDATE_BRANCH
from cutty.projects.link import linkproject2
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.loadtemplate import Template as Template2
from cutty.services.loadtemplate import TemplateMetadata
from cutty.util.git import Repository
from tests.util.git import updatefile


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
def template2(template: Template) -> Template2:
    """Fixture for a `Template` instance."""
    location = "https://example.com/template"
    metadata = TemplateMetadata(location, None, None, template.name, template.revision)
    return Template2(metadata, template.path)


@pytest.fixture
def createproject(template: Template) -> CreateProject:
    """Fixture for a `createproject` function."""

    def _(project: Path) -> Template:
        (project / "cutty.json").touch()
        return template

    return _


def test_linkproject2_commit(
    project: Repository, createproject: CreateProject, template2: Template2
) -> None:
    """It creates a commit on the current branch."""
    tip = project.head.commit

    linkproject2(project, createproject, template2)

    assert [tip] == project.head.commit.parents


def test_linkproject2_commit_message(
    project: Repository, createproject: CreateProject, template2: Template2
) -> None:
    """It uses a commit message indicating the linkage."""
    linkproject2(project, createproject, template2)

    assert "link" in project.head.commit.message.lower()


def test_linkproject2_commit_message_template(
    project: Repository,
    createproject: CreateProject,
    template2: Template2,
    template: Template,
) -> None:
    """It includes the template name in the commit message."""
    linkproject2(project, createproject, template2)

    assert template.name in project.head.commit.message


def test_linkproject2_commit_message_revision(
    project: Repository, template2: Template2, template: Template
) -> None:
    """It includes the template name in the commit message."""
    template = dataclasses.replace(template, revision="1.0.0")
    template2 = dataclasses.replace(
        template2, metadata=dataclasses.replace(template2.metadata, revision="1.0.0")
    )

    def createproject(project: Path) -> Template:
        (project / "cutty.json").touch()
        return template

    linkproject2(project, createproject, template2)

    assert template.revision in project.head.commit.message


def test_linkproject2_latest_branch(
    project: Repository, createproject: CreateProject, template2: Template2
) -> None:
    """It creates the latest branch."""
    updatefile(project.path / "initial")

    linkproject2(project, createproject, template2)

    assert LATEST_BRANCH in project.heads


def test_linkproject2_latest_branch_commit_message(
    project: Repository, createproject: CreateProject, template2: Template2
) -> None:
    """It uses a commit message indicating an initial import."""
    updatefile(project.path / "initial")

    linkproject2(project, createproject, template2)

    assert "initial" in project.heads[LATEST_BRANCH].message.lower()


def test_linkproject2_latest_branch_commit_message_update(
    project: Repository, createproject: CreateProject, template2: Template2
) -> None:
    """It uses a commit message indicating an update if the branch exists."""
    project.heads.create(LATEST_BRANCH)

    updatefile(project.path / "initial")

    linkproject2(project, createproject, template2)

    assert "update" in project.heads[LATEST_BRANCH].message.lower()


def test_linkproject2_update_branch(
    project: Repository, createproject: CreateProject, template2: Template2
) -> None:
    """It creates the update branch."""
    updatefile(project.path / "initial")

    linkproject2(project, createproject, template2)

    assert UPDATE_BRANCH in project.heads
