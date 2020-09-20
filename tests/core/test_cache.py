"""Tests for the cache module."""
from pathlib import Path

from ..utils import commit
from cutty.core import git
from cutty.core.cache import Cache


def test_repository_clones(user_cache_dir: Path, template: git.Repository) -> None:
    """It clones the repository if it does not exist."""
    cache = Cache(user_cache_dir)
    location = str(template.path)
    with cache.load(location) as loaded_template:
        mirror = git.Repository(loaded_template.repository)
        origin = mirror.get_remote_url("origin")
        assert origin == location


def test_repository_updates(user_cache_dir: Path, template: git.Repository) -> None:
    """It updates the repository if it exists."""
    cache = Cache(user_cache_dir)
    location = str(template.path)

    with cache.load(location):
        pass

    head = commit(template)
    template.tag("v1.0.1")

    with cache.load(location) as loaded_template:
        mirror = git.Repository(loaded_template.repository)
        assert mirror.rev_parse("HEAD") == head


def test_worktree_creates(user_cache_dir: Path, template: git.Repository) -> None:
    """It creates a worktree."""
    cache = Cache(user_cache_dir)
    head = template.rev_parse("HEAD")
    location = str(template.path)

    with cache.load(location, revision="HEAD") as loaded_template:
        mirror = git.Repository(loaded_template.repository)
        assert mirror.rev_parse("HEAD") == head


def test_worktree_removes(user_cache_dir: Path, template: git.Repository) -> None:
    """It removes the worktree after use."""
    cache = Cache(user_cache_dir)
    location = str(template.path)

    with cache.load(location, revision="HEAD") as loaded_template:
        pass

    assert not loaded_template.repository.exists()
