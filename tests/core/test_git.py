"""Tests for the git module."""
from pathlib import Path

import pytest

from ..utils import commit
from cutty.core import git


@pytest.fixture
def mirror(tmp_path: Path, repository: git.Repository) -> git.Repository:
    """Mirror repository in a temporary directory."""
    return git.Repository.clone(str(repository.path), tmp_path / "mirror", mirror=True)


def test_tags(repository: git.Repository) -> None:
    """It returns the tags."""
    commit(repository)
    repository.tag("v1.0.0")
    assert repository.tags() == ["v1.0.0"]


def test_worktree(
    tmp_path: Path, repository: git.Repository, mirror: git.Repository
) -> None:
    """It adds and removes a worktree."""
    (repository.path / "README").touch()
    repository.add("README")
    commit(repository)
    mirror.update_remote()
    path = tmp_path / "worktree"
    worktree = mirror.add_worktree(path, "HEAD", detach=True)
    assert (worktree.path / "README").is_file()
    mirror.remove_worktree(path)
    assert not (worktree.path / "README").exists()


def test_rev_parse(repository: git.Repository) -> None:
    """It returns the SHA1 hash."""
    commit(repository)
    assert repository.rev_parse("HEAD")


def test_clone_non_existing_directory() -> None:
    """It raises an error."""
    with pytest.raises(git.Error, match="does not exist"):
        git.Repository.clone("/no/such/directory")


def test_error_without_stderr(repository: git.Repository) -> None:
    """It reports the exit status."""
    with pytest.raises(git.Error, match="exit status"):
        repository.git("rev-parse", "--verify", "--quiet", "no-such-revision")
