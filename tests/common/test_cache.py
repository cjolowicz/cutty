"""Tests for the cache module."""
from pathlib import Path

from ..utils import commit
from cutty import git
from cutty.common.cache import Cache


def test_repository_clones(user_cache_dir: Path, repository: git.Repository) -> None:
    """It clones the repository if it does not exist."""
    commit(repository)
    location = str(repository.path)
    with Cache.load(location) as cache:
        mirror = git.Repository(cache.repository)
        origin = mirror.get_remote_url("origin")
        assert origin == location


def test_repository_updates(user_cache_dir: Path, repository: git.Repository) -> None:
    """It updates the repository if it exists."""
    commit(repository)
    location = str(repository.path)

    with Cache.load(location) as cache:
        pass

    head = commit(repository)

    with Cache.load(location) as cache:
        mirror = git.Repository(cache.repository)
        assert mirror.rev_parse("HEAD") == head


def test_worktree_creates(user_cache_dir: Path, repository: git.Repository) -> None:
    """It creates a worktree."""
    head = commit(repository)
    location = str(repository.path)

    with Cache.load(location, revision="HEAD") as cache:
        mirror = git.Repository(cache.repository)
        assert mirror.rev_parse("HEAD") == head


def test_worktree_removes(user_cache_dir: Path, repository: git.Repository) -> None:
    """It removes the worktree after use."""
    commit(repository)
    location = str(repository.path)

    with Cache.load(location, revision="HEAD") as cache:
        pass

    assert not cache.repository.exists()
