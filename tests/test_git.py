"""Tests for the git module."""
from pathlib import Path

import pytest

from .utils import commit
from cutty import git


@pytest.fixture
def mirror(tmp_path: Path, repository: git.Repository) -> git.Repository:
    """Mirror repository in a temporary directory."""
    path = tmp_path / "mirror"
    git.git("clone", "--mirror", str(repository.path), str(path))
    return git.Repository(path)


def test_tags(repository: git.Repository) -> None:
    """It returns the tags."""
    commit(repository)
    repository.git("tag", "v1.0.0")
    assert repository.tags() == ["v1.0.0"]


def test_worktree(
    tmp_path: Path, repository: git.Repository, mirror: git.Repository
) -> None:
    """It adds and removes a worktree."""
    (repository.path / "README").touch()
    repository.git("add", "README")
    commit(repository)
    mirror.git("remote", "update")
    path = tmp_path / "worktree"
    worktree = mirror.add_worktree(path, "HEAD", detach=True)
    assert (worktree.path / "README").is_file()
    mirror.remove_worktree(path)
    assert not (worktree.path / "README").exists()


def test_rev_parse(repository: git.Repository) -> None:
    """It returns the SHA1 hash."""
    commit(repository)
    assert repository.rev_parse("HEAD")
