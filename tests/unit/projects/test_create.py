"""Unit tests for cutty.projects.create."""
import dataclasses
import pathlib

from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.storage import FileStorage
from cutty.projects.common import LATEST_BRANCH
from cutty.projects.create import creategitrepository
from cutty.services.loadtemplate import TemplateMetadata
from cutty.util.git import Repository


def test_repository(project: pathlib.Path, template: TemplateMetadata) -> None:
    """It creates a repository."""
    creategitrepository(project, template)

    Repository.open(project)  # does not raise


def test_commit(project: pathlib.Path, template: TemplateMetadata) -> None:
    """It creates a commit."""
    creategitrepository(project, template)

    repository = Repository.open(project)
    repository.head.commit  # does not raise


def test_commit_message_template(
    project: pathlib.Path, template: TemplateMetadata
) -> None:
    """It includes the template name in the commit message."""
    creategitrepository(project, template)

    repository = Repository.open(project)
    assert template.name in repository.head.commit.message


def test_commit_message_revision(
    project: pathlib.Path, template: TemplateMetadata
) -> None:
    """It includes the revision in the commit message."""
    template = dataclasses.replace(template, revision="1.0.0")
    creategitrepository(project, template)

    repository = Repository.open(project)
    assert template.revision in repository.head.commit.message


def test_existing_repository(
    storage: FileStorage,
    file: RegularFile,
    projectpath: pathlib.Path,
    template: TemplateMetadata,
) -> None:
    """It creates the commit in an existing repository."""
    repository = Repository.init(projectpath)
    repository.commit()

    with storage:
        storage.add(file)

    creategitrepository(projectpath, template)

    assert file.path.name in repository.head.commit.tree


def test_branch(project: pathlib.Path, template: TemplateMetadata) -> None:
    """It creates a branch pointing to the initial commit."""
    creategitrepository(project, template)

    repository = Repository.open(project)
    assert repository.head.commit == repository.heads[LATEST_BRANCH]


def test_branch_not_checked_out(
    project: pathlib.Path, template: TemplateMetadata
) -> None:
    """It does not check out the `latest` branch."""
    creategitrepository(project, template)

    repository = Repository.open(project)
    assert repository.head.name != LATEST_BRANCH
