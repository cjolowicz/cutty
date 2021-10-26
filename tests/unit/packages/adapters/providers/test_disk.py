"""Unit tests for cutty.packages.adapters.providers.disk."""
from pathlib import Path

import pytest

from cutty.packages.adapters.providers.disk import diskprovider
from cutty.packages.domain.locations import asurl


@pytest.fixture
def repositorypath(tmp_path: Path) -> Path:
    """Fixture for a package repository."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").write_text("Lorem")
    return path


def test_happy(repositorypath: Path) -> None:
    """It provides a repository from a local directory."""
    url = asurl(repositorypath)
    repository = diskprovider.provide(url)
    assert repository is not None

    with repository.get() as package:
        text = (package.path / "marker").read_text()
        assert text == "Lorem"


def test_revision(repositorypath: Path) -> None:
    """It raises an exception when passed a revision."""
    url = asurl(repositorypath)
    with pytest.raises(Exception):
        diskprovider.provide(url, "v1.0")
