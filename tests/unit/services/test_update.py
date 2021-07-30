"""Unit tests for cutty.services.update."""
from pathlib import Path

import pygit2
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
    repository: pygit2.Repository, path: Path, *, ours: str, theirs: str
) -> None:
    """Create an update conflict."""
    main = repository.head
    update, _ = createbranches(Repository(repository), UPDATE_BRANCH, LATEST_BRANCH)

    repository.checkout(update)
    updatefile(path, theirs)

    repository.checkout(main)
    updatefile(path, ours)

    with pytest.raises(Exception, match=path.name):
        Repository(repository).cherrypick(update.name, message="")


def test_continueupdate_commits_changes(
    repository: Repository, repositorypath: Path, path: Path
) -> None:
    """It commits the changes."""
    createconflict(repository.repository, path, ours="a", theirs="b")
    resolveconflicts(repositorypath, path, Side.THEIRS)

    with chdir(repositorypath):
        continueupdate()

    blob = repository.repository.head.peel().tree / path.name
    assert blob.data == b"b"


def test_continueupdate_fastforwards_latest(
    repository: Repository, repositorypath: Path, path: Path
) -> None:
    """It updates the latest branch to the tip of the update branch."""
    createconflict(repository.repository, path, ours="a", theirs="b")
    resolveconflicts(repositorypath, path, Side.THEIRS)

    with chdir(repositorypath):
        continueupdate()

    branches = repository.repository.branches
    assert branches[LATEST_BRANCH].peel() == branches[UPDATE_BRANCH].peel()


def test_skipupdate_fastforwards_latest(
    repository: Repository, repositorypath: Path, path: Path
) -> None:
    """It fast-forwards the latest branch to the tip of the update branch."""
    createconflict(repository.repository, path, ours="a", theirs="b")

    updatehead = repository.repository.branches[UPDATE_BRANCH].peel()

    with chdir(repositorypath):
        skipupdate()

    assert repository.repository.branches[LATEST_BRANCH].peel() == updatehead


def test_abortupdate_rewinds_update_branch(
    repository: Repository, repositorypath: Path, path: Path
) -> None:
    """It resets the update branch to the tip of the latest branch."""
    createconflict(repository.repository, path, ours="a", theirs="b")

    branches = repository.repository.branches
    latesthead = branches[LATEST_BRANCH].peel()

    with chdir(repositorypath):
        abortupdate()

    assert (
        branches[LATEST_BRANCH].peel() == latesthead == branches[UPDATE_BRANCH].peel()
    )
