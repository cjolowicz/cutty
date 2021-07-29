"""Unit tests for cutty.util.git."""
import string
from collections.abc import Iterator
from pathlib import Path

import pygit2
import pytest

from cutty.services.update import cherrypick
from cutty.util.git import createworktree
from tests.util.git import commit
from tests.util.git import removefile
from tests.util.git import updatefile


@pytest.fixture
def repositorypath(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    repositorypath = tmp_path / "repository"
    pygit2.init_repository(repositorypath)
    commit(repositorypath)
    return repositorypath


@pytest.fixture
def repository(repositorypath: Path) -> pygit2.Repository:
    """Fixture for a repository."""
    return pygit2.Repository(repositorypath)


@pytest.fixture
def paths(repositorypath: Path) -> Iterator[Path]:
    """Return arbitrary paths in the repository."""
    return (repositorypath / letter for letter in string.ascii_letters)


@pytest.fixture
def path(paths: Iterator[Path]) -> Path:
    """Return an arbitrary path in the repository."""
    return next(paths)


def createbranch(repository: pygit2.Repository, name: str) -> pygit2.Branch:
    """Create a branch at HEAD."""
    return repository.branches.create(name, repository.head.peel())


def test_createworktree_creates_worktree(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It creates a worktree."""
    createbranch(repository, "branch")

    with createworktree(repositorypath, "branch") as worktree:
        assert (worktree / ".git").is_file()


def test_createworktree_removes_worktree_on_exit(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It removes the worktree on exit."""
    createbranch(repository, "branch")

    with createworktree(repositorypath, "branch") as worktree:
        pass

    assert not worktree.is_dir()


def test_createworktree_does_checkout(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It checks out a working tree."""
    updatefile(path)
    createbranch(repository, "branch")

    with createworktree(repositorypath, "branch") as worktree:
        assert (worktree / path.name).is_file()


def test_createworktree_no_checkout(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It creates a worktree without checking out the files."""
    updatefile(path)
    createbranch(repository, "branch")

    with createworktree(repositorypath, "branch", checkout=False) as worktree:
        assert not (worktree / path.name).is_file()


def test_cherrypick_adds_file(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It cherry-picks the commit onto the current branch."""
    main = repository.head
    branch = createbranch(repository, "branch")

    repository.checkout(branch)
    updatefile(path)

    repository.checkout(main)
    assert not path.is_file()

    cherrypick(repositorypath, branch.name)
    assert path.is_file()


def test_cherrypick_conflict_edit(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It raises an exception when both sides modified the file."""
    main = repository.head
    branch = createbranch(repository, "branch")

    repository.checkout(branch)
    updatefile(path, "a")

    repository.checkout(main)
    updatefile(path, "b")

    with pytest.raises(Exception, match=path.name):
        cherrypick(repositorypath, branch.name)


def test_cherrypick_conflict_deletion(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It raises an exception when one side modified and the other deleted the file."""
    updatefile(path, "a")

    main = repository.head
    branch = createbranch(repository, "branch")

    repository.checkout(branch)
    updatefile(path, "b")

    repository.checkout(main)
    removefile(path)

    with pytest.raises(Exception, match=path.name):
        cherrypick(repositorypath, branch.name)
