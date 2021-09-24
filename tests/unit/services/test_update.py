"""Unit tests for cutty.services.update."""
from pathlib import Path

import pytest

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path as VirtualPath
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.git import LATEST_BRANCH
from cutty.services.git import UPDATE_BRANCH
from cutty.services.update import abortupdate
from cutty.services.update import continueupdate
from cutty.services.update import CreateProject
from cutty.services.update import skipupdate
from cutty.services.update import updateproject
from cutty.util.git import Repository
from tests.util.files import chdir
from tests.util.git import createbranches
from tests.util.git import resolveconflicts
from tests.util.git import Side
from tests.util.git import updatefile


pytest_plugins = ["tests.fixtures.git"]


def createconflict(
    repository: Repository, path: Path, *, ours: str, theirs: str
) -> None:
    """Create an update conflict."""
    main = repository.head
    update, _ = createbranches(repository, UPDATE_BRANCH, LATEST_BRANCH)

    repository.checkout(update)
    updatefile(path, theirs)

    repository.checkout(main)
    updatefile(path, ours)

    with pytest.raises(Exception, match=path.name):
        repository.cherrypick(update.commit)


def test_continueupdate_commits_changes(repository: Repository, path: Path) -> None:
    """It commits the changes."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    with chdir(repository.path):
        continueupdate()

    blob = repository.head.commit.tree / path.name
    assert blob.data == b"b"


def test_continueupdate_preserves_metainfo(repository: Repository, path: Path) -> None:
    """It preserves the original commit message."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    with chdir(repository.path):
        continueupdate()

    assert repository.heads[UPDATE_BRANCH].message == repository.head.commit.message


def test_continueupdate_fastforwards_latest(repository: Repository, path: Path) -> None:
    """It updates the latest branch to the tip of the update branch."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    with chdir(repository.path):
        continueupdate()

    assert repository.heads[LATEST_BRANCH] == repository.heads[UPDATE_BRANCH]


def test_continueupdate_works_after_commit(repository: Repository, path: Path) -> None:
    """It updates the latest branch even if the cherry-pick is no longer in progress."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    # The user invokes `git cherry-pick --continue` before `cutty update --continue`.
    repository.commit()

    with chdir(repository.path):
        continueupdate()

    assert repository.heads[LATEST_BRANCH] == repository.heads[UPDATE_BRANCH]


def test_continueupdate_state_cleanup(repository: Repository, path: Path) -> None:
    """It removes CHERRY_PICK_HEAD."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    with chdir(repository.path):
        continueupdate()

    assert repository.cherrypickhead is None


def test_skipupdate_fastforwards_latest(repository: Repository, path: Path) -> None:
    """It fast-forwards the latest branch to the tip of the update branch."""
    createconflict(repository, path, ours="a", theirs="b")

    updatehead = repository.heads[UPDATE_BRANCH]

    with chdir(repository.path):
        skipupdate()

    assert repository.heads[LATEST_BRANCH] == updatehead


def test_abortupdate_rewinds_update_branch(repository: Repository, path: Path) -> None:
    """It resets the update branch to the tip of the latest branch."""
    createconflict(repository, path, ours="a", theirs="b")

    latesthead = repository.heads[LATEST_BRANCH]

    with chdir(repository.path):
        abortupdate()

    assert (
        repository.heads[LATEST_BRANCH] == latesthead == repository.heads[UPDATE_BRANCH]
    )


@pytest.fixture
def project(repository: Repository) -> Repository:
    """Fixture for a project repository."""
    repository.heads.create(LATEST_BRANCH)
    return repository


@pytest.fixture
def createproject() -> CreateProject:
    """Fixture for a `createproject` function."""

    def _(project: Path) -> Template:
        (project / "marker").touch()
        templatepath = VirtualPath(filesystem=DictFilesystem({}))
        return Template("template", templatepath, None)

    return _


def test_updateproject(project: Repository, createproject: CreateProject) -> None:
    """It works."""
    updateproject(project.path, createproject)
