"""Git-related fixtures."""
import string
from collections.abc import Iterator
from pathlib import Path

import pytest

from cutty.util.git import Repository


@pytest.fixture
def repository(tmp_path: Path) -> Repository:
    """Fixture for a repository."""
    repository = Repository.init(tmp_path / "repository")
    repository.commit()
    return repository


@pytest.fixture
def repositorypath(repository: Repository) -> Path:
    """Fixture for a repository."""
    return repository.path


@pytest.fixture
def paths(repository: Repository) -> Iterator[Path]:
    """Return arbitrary paths in the repository."""
    return (repository.path / letter for letter in string.ascii_letters)


@pytest.fixture
def path(paths: Iterator[Path]) -> Path:
    """Return an arbitrary path in the repository."""
    return next(paths)
