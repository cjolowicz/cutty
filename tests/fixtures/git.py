"""Git-related fixtures."""
import string
from collections.abc import Iterator
from pathlib import Path

import pytest

from cutty.util.git import Repository


@pytest.fixture
def repositorypath(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    repositorypath = tmp_path / "repository"
    repository = Repository.init(repositorypath)
    repository.commit()
    return repositorypath


@pytest.fixture
def repository(repositorypath: Path) -> Repository:
    """Fixture for a repository."""
    return Repository.open(repositorypath)


@pytest.fixture
def paths(repositorypath: Path) -> Iterator[Path]:
    """Return arbitrary paths in the repository."""
    return (repositorypath / letter for letter in string.ascii_letters)


@pytest.fixture
def path(paths: Iterator[Path]) -> Path:
    """Return an arbitrary path in the repository."""
    return next(paths)
