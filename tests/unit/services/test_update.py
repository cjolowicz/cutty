"""Unit tests for cutty.services.update."""
from pathlib import Path

import pytest

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.services.update import abortupdate
from cutty.services.update import continueupdate
from cutty.services.update import skipupdate
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
    main = repository.branches.head
    update, _ = createbranches(repository, UPDATE_BRANCH, LATEST_BRANCH)

    repository.checkout(update)
    updatefile(path, theirs)

    repository.checkout(main)
    updatefile(path, ours)

    with pytest.raises(Exception, match=path.name):
        repository.cherrypick2(update.commit, message="")


def test_continueupdate_commits_changes(repository: Repository, path: Path) -> None:
    """It commits the changes."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    with chdir(repository.path):
        continueupdate()

    blob = repository.head.peel().tree / path.name
    assert blob.data == b"b"


def test_continueupdate_fastforwards_latest(repository: Repository, path: Path) -> None:
    """It updates the latest branch to the tip of the update branch."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    with chdir(repository.path):
        continueupdate()

    assert repository.branches[LATEST_BRANCH] == repository.branches[UPDATE_BRANCH]


def test_skipupdate_fastforwards_latest(repository: Repository, path: Path) -> None:
    """It fast-forwards the latest branch to the tip of the update branch."""
    createconflict(repository, path, ours="a", theirs="b")

    updatehead = repository.branches[UPDATE_BRANCH]

    with chdir(repository.path):
        skipupdate()

    assert repository.branches[LATEST_BRANCH] == updatehead


def test_abortupdate_rewinds_update_branch(repository: Repository, path: Path) -> None:
    """It resets the update branch to the tip of the latest branch."""
    createconflict(repository, path, ours="a", theirs="b")

    latesthead = repository.branches[LATEST_BRANCH]

    with chdir(repository.path):
        abortupdate()

    assert (
        repository.branches[LATEST_BRANCH]
        == latesthead
        == repository.branches[UPDATE_BRANCH]
    )
