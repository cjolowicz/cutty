"""Unit tests for cutty.repositories2.adapters.providers.disk."""
from pathlib import Path

import pytest

from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories2.adapters.providers.disk import diskprovider
from cutty.repositories2.domain.urls import asurl


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").write_text("Lorem")
    return path


def test_diskprovider_happy(repository: Path) -> None:
    """It provides a repository from a local directory."""
    url = asurl(repository)
    filesystem = diskprovider(url, None)
    assert filesystem is not None

    text = filesystem.read_text(PurePath("marker"))
    assert text == "Lorem"


def test_diskprovider_revision(repository: Path) -> None:
    """It raises an exception when passed a revision."""
    url = asurl(repository)
    with pytest.raises(Exception):
        diskprovider(url, "v1.0")
