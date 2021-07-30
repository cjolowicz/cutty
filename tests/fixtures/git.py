"""Git-related fixtures."""
import string
from collections.abc import Iterator
from pathlib import Path

import pygit2
import pytest

from cutty.util.git import commit


@pytest.fixture
def repositorypath(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    repositorypath = tmp_path / "repository"
    repository = pygit2.init_repository(repositorypath)
    commit(repository)
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
