"""Tests for git fixtures."""
from collections.abc import Iterator
from pathlib import Path

from cutty.util.git import Repository


pytest_plugins = ["tests.fixtures.git"]


def test_paths(repository: Repository, paths: Iterator[Path]) -> None:
    """It returns paths in the repository."""
    for path in paths:
        assert repository.path == path.parent
