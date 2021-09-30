"""Unit tests for cutty.services.link."""
import dataclasses
from pathlib import Path

import pytest

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path as VirtualPath
from cutty.projects.common import CreateProject2
from cutty.projects.common import LATEST_BRANCH
from cutty.projects.common import UPDATE_BRANCH
from cutty.projects.link import linkproject
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
def template() -> Template2:
    """Fixture for a `Template` instance."""
    templatepath = VirtualPath(filesystem=DictFilesystem({}))
    template = Template("template", templatepath, None)
    location = "https://example.com/template"
    metadata = TemplateMetadata(location, None, None, template.name, template.revision)
    return Template2(metadata, template.path)


@pytest.fixture
def createproject() -> CreateProject2:
    """Fixture for a `createproject` function."""

    def _(project: Path) -> None:
        (project / "cutty.json").touch()

    return _


def test_linkproject_commit(
    project: Repository, createproject: CreateProject2, template2: Template2
) -> None:
    """It creates a commit on the current branch."""
    tip = project.head.commit

    linkproject(project, createproject, template2)

    assert [tip] == project.head.commit.parents


def test_linkproject_commit_message(
    project: Repository, createproject: CreateProject2, template2: Template2
) -> None:
    """It uses a commit message indicating the linkage."""
    linkproject(project, createproject, template2)

    assert "link" in project.head.commit.message.lower()


def test_linkproject_commit_message_template(
    project: Repository,
    createproject: CreateProject2,
    template2: Template2,
) -> None:
    """It includes the template name in the commit message."""
    linkproject(project, createproject, template2)

    assert template2.metadata.name in project.head.commit.message


def test_linkproject_commit_message_revision(
    project: Repository, template2: Template2
) -> None:
    """It includes the template name in the commit message."""
    template2 = dataclasses.replace(
        template2, metadata=dataclasses.replace(template2.metadata, revision="1.0.0")
    )

    def createproject(project: Path) -> None:
        (project / "cutty.json").touch()

    linkproject(project, createproject, template2)

    assert template2.metadata.revision in project.head.commit.message


def test_linkproject_latest_branch(
    project: Repository, createproject: CreateProject2, template2: Template2
) -> None:
    """It creates the latest branch."""
    updatefile(project.path / "initial")

    linkproject(project, createproject, template2)

    assert LATEST_BRANCH in project.heads


def test_linkproject_latest_branch_commit_message(
    project: Repository, createproject: CreateProject2, template2: Template2
) -> None:
    """It uses a commit message indicating an initial import."""
    updatefile(project.path / "initial")

    linkproject(project, createproject, template2)

    assert "initial" in project.heads[LATEST_BRANCH].message.lower()


def test_linkproject_latest_branch_commit_message_update(
    project: Repository, createproject: CreateProject2, template2: Template2
) -> None:
    """It uses a commit message indicating an update if the branch exists."""
    project.heads.create(LATEST_BRANCH)

    updatefile(project.path / "initial")

    linkproject(project, createproject, template2)

    assert "update" in project.heads[LATEST_BRANCH].message.lower()


def test_linkproject_update_branch(
    project: Repository, createproject: CreateProject2, template2: Template2
) -> None:
    """It creates the update branch."""
    updatefile(project.path / "initial")

    linkproject(project, createproject, template2)

    assert UPDATE_BRANCH in project.heads
