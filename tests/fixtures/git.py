"""Git-related fixtures."""
import string
from collections.abc import Iterator
from pathlib import Path
from textwrap import dedent
from typing import Protocol

import pytest

from cutty.util.git import Repository


@pytest.fixture
def repository(tmp_path: Path) -> Repository:
    """Fixture for a repository."""
    repository = Repository.init(tmp_path / "repository")
    repository.commit()
    return repository


@pytest.fixture
def paths(repository: Repository) -> Iterator[Path]:
    """Return arbitrary paths in the repository."""
    return (repository.path / letter for letter in string.ascii_letters)


@pytest.fixture
def path(paths: Iterator[Path]) -> Path:
    """Return an arbitrary path in the repository."""
    return next(paths)


class UpdateFile(Protocol):
    """Protocol for the `updatefile` fixture."""

    def __call__(self, path: Path, text: str = "") -> None:
        """Function signature."""


@pytest.fixture
def updatefile(repository: Repository) -> UpdateFile:
    """Fixture for adding or updating a repository file.

    NOTE: We cannot use `Repository.discover` here because `Repository`
    instances in client code would likely miss our changes to the index.
    """

    def _updatefile(path: Path, text: str = "") -> None:
        verb = "Update" if path.exists() else "Add"

        path.write_text(dedent(text).lstrip())

        repository.commit(message=f"{verb} {path.name}")

    return _updatefile
