"""Unit tests for cutty.services.create."""
import pathlib
from typing import Optional

import pygit2
import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.observers import FileStorageObserver
from cutty.filestorage.domain.observers import observe
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.purepath import PurePath
from cutty.services.create import creategitrepository
from cutty.services.create import LATEST_BRANCH
from cutty.services.create import UPDATE_BRANCH
from cutty.util.git import Repository
from tests.util.git import createbranches


class GitRepositoryObserver(FileStorageObserver):
    """Storage observer creating a git repository."""

    def __init__(
        self,
        *,
        project: pathlib.Path,
        template: str = "template",
        revision: Optional[str] = None,
    ) -> None:
        """Initialize."""
        self.project = project
        self.template = template
        self.revision = revision

    def commit(self) -> None:
        """A storage transaction was completed."""
        creategitrepository(self.project, self.template, self.revision)


@pytest.fixture
def project(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture for a project path."""
    return tmp_path / "project"


@pytest.fixture
def storage2(project: pathlib.Path) -> FileStorage:
    """Fixture for a storage."""
    return DiskFileStorage(project.parent)


@pytest.fixture
def storage(project: pathlib.Path) -> FileStorage:
    """Fixture for a storage."""
    observer = GitRepositoryObserver(project=project)
    storage = DiskFileStorage(project.parent)
    return observe(storage, observer)


@pytest.fixture
def file(project: pathlib.Path) -> RegularFile:
    """Fixture for a regular file."""
    path = PurePath(project.name, "README.md")
    return RegularFile(path, b"")


def test_repository(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It creates a repository."""
    with storage2:
        storage2.add(file)

    creategitrepository(project, "template", None)

    Repository.open(project)  # does not raise


def test_commit(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It creates a commit."""
    with storage2:
        storage2.add(file)

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    repository.head.commit  # does not raise


def test_commit_message_template(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It includes the template name in the commit message."""
    with storage2:
        storage2.add(file)

    template = "awesome-template"
    creategitrepository(project, template, None)

    repository = Repository.open(project)
    assert template in repository.head.commit.message


def test_commit_message_revision(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It includes the revision in the commit message."""
    with storage2:
        storage2.add(file)

    revision = "1.0.0"
    creategitrepository(project, "template", revision)

    repository = Repository.open(project)
    assert revision in repository.head.commit.message


def test_index(storage2: FileStorage, file: RegularFile, project: pathlib.Path) -> None:
    """It updates the index."""
    with storage2:
        storage2.add(file)

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    assert file.path.name in repository._repository.index


def tree(repository: Repository) -> pygit2.Tree:
    """Return the tree at the HEAD of the repository."""
    return repository.head.commit.tree


def test_hook_edits(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It commits file modifications applied by hooks."""
    with storage2:
        storage2.add(file)
        (project / file.path.name).write_bytes(b"teapot")

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    blob = tree(repository) / file.path.name
    assert b"teapot" == blob.data


def test_hook_deletes(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It does not commit files deleted by hooks."""
    with storage2:
        storage2.add(file)
        (project / file.path.name).unlink()

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    assert file.path.name not in tree(repository)


def test_hook_additions(storage2: FileStorage, project: pathlib.Path) -> None:
    """It commits files created by hooks."""
    with storage2:
        project.mkdir()
        (project / "marker").touch()

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    assert "marker" in tree(repository)


def test_existing_repository(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It creates the commit in an existing repository."""
    repository = Repository.init(project)
    repository.commit()

    with storage2:
        storage2.add(file)

    creategitrepository(project, "template", None)

    assert file.path.name in tree(repository)


def test_branch(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It creates a branch pointing to the initial commit."""
    with storage2:
        storage2.add(file)

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    assert repository.head.commit == repository.heads[LATEST_BRANCH]


def test_branch_not_checked_out(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It does not check out the `latest` branch."""
    with storage2:
        storage2.add(file)

    creategitrepository(project, "template", None)

    repository = Repository.open(project)
    assert repository.head.name != LATEST_BRANCH


def test_existing_branch(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It updates the `update` branch if it exists."""
    repository = Repository.init(project)
    repository.commit()

    branch = repository.heads.create(UPDATE_BRANCH)
    repository.checkout(branch)

    with storage2:
        storage2.add(file)

    creategitrepository(project, "template", None)

    assert file.path.name in tree(repository)


def test_existing_branch_not_head(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It raises an exception if `update` exists but HEAD points elsewhere."""
    repository = Repository.init(project)
    repository.commit()

    repository.heads.create(UPDATE_BRANCH)

    with pytest.raises(Exception):
        with storage2:
            storage2.add(file)

        creategitrepository(project, "template", None)

    assert file.path.name not in tree(repository)


def test_existing_branch_commit_message(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It uses a different commit message on updates."""
    repository = Repository.init(project)
    repository.commit()

    update, _ = createbranches(repository, UPDATE_BRANCH, LATEST_BRANCH)
    repository.checkout(update)

    with storage2:
        storage2.add(file)

    creategitrepository(project, "template", None)

    assert "initial" not in repository.head.commit.message.lower()


def test_existing_branch_commit_message_template(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It includes the template name in the commit message."""
    repository = Repository.init(project)
    repository.commit()

    update, _ = createbranches(repository, UPDATE_BRANCH, LATEST_BRANCH)
    repository.checkout(update)

    with storage2:
        storage2.add(file)

    template = "awesome-template"
    creategitrepository(project, template, None)

    assert template in repository.head.commit.message


def test_existing_branch_commit_message_revision(
    storage2: FileStorage, file: RegularFile, project: pathlib.Path
) -> None:
    """It includes the revision in the commit message."""
    repository = Repository.init(project)
    repository.commit()

    update, _ = createbranches(repository, UPDATE_BRANCH, LATEST_BRANCH)
    repository.checkout(update)

    with storage2:
        storage2.add(file)

    revision = "1.0.0"
    creategitrepository(project, "template", revision)

    assert revision in repository.head.commit.message


def test_existing_branch_no_changes(
    storage2: FileStorage, project: pathlib.Path
) -> None:
    """It does not create an empty commit."""
    repository = Repository.init(project)
    repository.commit()

    branch = repository.heads.create(UPDATE_BRANCH)
    repository.checkout(branch)
    oldhead = repository.head.commit

    with storage2:
        pass

    creategitrepository(project, "template", None)

    assert oldhead == repository.head.commit
