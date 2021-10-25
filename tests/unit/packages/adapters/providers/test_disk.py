"""Unit tests for cutty.packages.adapters.providers.disk."""
from pathlib import Path

import pytest

from cutty.packages.adapters.providers.disk import diskprovider
from cutty.packages.domain.locations import asurl


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").write_text("Lorem")
    return path


def test_happy(repository: Path) -> None:
    """It provides a repository from a local directory."""
    url = asurl(repository)
    repository2 = diskprovider(url)
    assert repository2 is not None

    text = (repository2.path / "marker").read_text()
    assert text == "Lorem"


def test_revision(repository: Path) -> None:
    """It raises an exception when passed a revision."""
    url = asurl(repository)
    with pytest.raises(Exception):
        diskprovider(url, "v1.0")
