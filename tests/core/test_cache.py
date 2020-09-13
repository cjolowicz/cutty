"""Tests for the cache module."""
from pathlib import Path

from ..utils import commit
from cutty.core import cache
from cutty.core import git


def test_repository_clones(user_cache_dir: Path, repository: git.Repository) -> None:
    """It clones the repository if it does not exist."""
    commit(repository)
    location = str(repository.path)
    with cache.load(location) as template:
        mirror = git.Repository(template.repository)
        origin = mirror.get_remote_url("origin")
        assert origin == location


def test_repository_updates(user_cache_dir: Path, repository: git.Repository) -> None:
    """It updates the repository if it exists."""
    commit(repository)
    location = str(repository.path)

    with cache.load(location) as template:
        pass

    head = commit(repository)

    with cache.load(location) as template:
        mirror = git.Repository(template.repository)
        assert mirror.rev_parse("HEAD") == head


def test_worktree_creates(user_cache_dir: Path, repository: git.Repository) -> None:
    """It creates a worktree."""
    head = commit(repository)
    location = str(repository.path)

    with cache.load(location, revision="HEAD") as template:
        mirror = git.Repository(template.repository)
        assert mirror.rev_parse("HEAD") == head


def test_worktree_removes(user_cache_dir: Path, repository: git.Repository) -> None:
    """It removes the worktree after use."""
    commit(repository)
    location = str(repository.path)

    with cache.load(location, revision="HEAD") as template:
        pass

    assert not template.repository.exists()
