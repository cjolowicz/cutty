"""Unit tests for cutty.services.update."""
import string
from collections.abc import Iterator
from pathlib import Path

import pygit2
import pytest

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.services.update import abortupdate
from cutty.services.update import cherrypick
from cutty.services.update import continueupdate
from cutty.services.update import resetmerge
from cutty.services.update import skipupdate
from tests.util.files import chdir
from tests.util.git import commit
from tests.util.git import resolveconflicts
from tests.util.git import Side
from tests.util.git import updatefile
from tests.util.git import updatefiles


@pytest.fixture
def repositorypath(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    repositorypath = tmp_path / "repository"
    pygit2.init_repository(repositorypath)
    commit(repositorypath)
    return repositorypath


@pytest.fixture
def paths(repositorypath: Path) -> Iterator[Path]:
    """Return arbitrary paths in the repository."""
    return (repositorypath / letter for letter in string.ascii_letters)


@pytest.fixture
def path(paths: Iterator[Path]) -> Path:
    """Return an arbitrary path in the repository."""
    return next(paths)


@pytest.fixture
def repository(repositorypath: Path) -> pygit2.Repository:
    """Fixture for a repository."""
    return pygit2.Repository(repositorypath)


def createbranch(repository: pygit2.Repository, name: str) -> pygit2.Branch:
    """Create a branch at HEAD."""
    return repository.branches.create(name, repository.head.peel())


def cuttybranches(
    repository: pygit2.Repository,
) -> tuple[pygit2.Reference, pygit2.Reference, pygit2.Reference]:
    """Return the current, the `cutty/latest`, and the `cutty/update` branches."""
    main = repository.head
    update = createbranch(repository, UPDATE_BRANCH)
    latest = createbranch(repository, LATEST_BRANCH)
    return main, update, latest


def createconflict(repositorypath: Path, path: Path, *, ours: str, theirs: str) -> None:
    """Create an update conflict."""
    repository = pygit2.Repository(repositorypath)
    main, update, _ = cuttybranches(repository)

    repository.checkout(update)
    updatefile(path, theirs)

    repository.checkout(main)
    updatefile(path, ours)

    with pytest.raises(Exception, match=path.name):
        cherrypick(repositorypath, update.name)


def test_continueupdate_commits_changes(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It commits the changes."""
    createconflict(repositorypath, path, ours="a", theirs="b")
    resolveconflicts(repositorypath, path, Side.THEIRS)

    with chdir(repositorypath):
        continueupdate()

    blob = repository.head.peel().tree / path.name
    assert blob.data == b"b"


def test_continueupdate_fastforwards_latest(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It updates the latest branch to the tip of the update branch."""
    createconflict(repositorypath, path, ours="a", theirs="b")
    resolveconflicts(repositorypath, path, Side.THEIRS)

    with chdir(repositorypath):
        continueupdate()

    branches = repository.branches
    assert branches[LATEST_BRANCH].peel() == branches[UPDATE_BRANCH].peel()


def test_resetmerge_restores_files_with_conflicts(
    repositorypath: Path, path: Path
) -> None:
    """It restores the conflicting files in the working tree to our version."""
    createconflict(repositorypath, path, ours="a", theirs="b")
    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert path.read_text() == "a"


def test_resetmerge_removes_added_files(
    repository: pygit2.Repository, repositorypath: Path, paths: Iterator[Path]
) -> None:
    """It removes files added by the cherry-picked commit."""
    main, update, _ = cuttybranches(repository)
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefiles({path1: "a", path2: ""})

    repository.checkout(main)
    updatefile(path1, "b")

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert not path2.exists()


def test_resetmerge_keeps_unrelated_additions(
    repository: pygit2.Repository, repositorypath: Path, paths: Iterator[Path]
) -> None:
    """It keeps additions of files that did not change in the update."""
    main, update, _ = cuttybranches(repository)
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")

    path2.touch()

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert path2.exists()


def test_resetmerge_keeps_unrelated_changes(
    repository: pygit2.Repository, repositorypath: Path, paths: Iterator[Path]
) -> None:
    """It keeps modifications to files that did not change in the update."""
    main, update, _ = cuttybranches(repository)
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")
    updatefile(path2)

    path2.write_text("c")

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert path2.read_text() == "c"


def test_resetmerge_keeps_unrelated_deletions(
    repository: pygit2.Repository, repositorypath: Path, paths: Iterator[Path]
) -> None:
    """It keeps deletions of files that did not change in the update."""
    main, update, _ = cuttybranches(repository)
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")
    updatefile(path2)

    path2.unlink()

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert not path2.exists()


def test_resetmerge_resets_index(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It resets the index to HEAD, removing conflicts."""
    createconflict(repositorypath, path, ours="a", theirs="b")

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert repository.index.write_tree() == repository.head.peel().tree.id


def test_skipupdate_fastforwards_latest(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It fast-forwards the latest branch to the tip of the update branch."""
    createconflict(repositorypath, path, ours="a", theirs="b")

    updatehead = repository.branches[UPDATE_BRANCH].peel()

    with chdir(repositorypath):
        skipupdate()

    assert repository.branches[LATEST_BRANCH].peel() == updatehead


def test_abortupdate_rewinds_update_branch(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It resets the update branch to the tip of the latest branch."""
    createconflict(repositorypath, path, ours="a", theirs="b")

    branches = repository.branches
    latesthead = branches[LATEST_BRANCH].peel()

    with chdir(repositorypath):
        abortupdate()

    assert (
        branches[LATEST_BRANCH].peel() == latesthead == branches[UPDATE_BRANCH].peel()
    )
