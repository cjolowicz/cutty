"""Unit tests for cutty.packages.adapters.fetchers.file."""
from pathlib import Path

import pytest
from yarl import URL

from cutty.errors import CuttyError
from cutty.packages.adapters.fetchers.file import filefetcher
from cutty.packages.domain.locations import asurl
from cutty.packages.domain.stores import Store


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").write_text("Lorem")
    return path


def test_directory_happy(repository: Path, store: Store) -> None:
    """It copies the filesystem tree."""
    url = asurl(repository)
    path = filefetcher.fetch(url, store)

    assert (path / "marker").read_text() == "Lorem"


def test_file_happy(repository: Path, store: Store) -> None:
    """It copies the file."""
    repository /= "marker"
    url = asurl(repository)
    path = filefetcher.fetch(url, store)

    assert path.read_text() == "Lorem"


def test_not_matched(store: Store, url: URL) -> None:
    """It returns None if the URL does not use the file scheme."""
    assert not filefetcher.match(url)


def test_directory_update(repository: Path, store: Store) -> None:
    """It removes files from a previous fetch."""
    url = asurl(repository)

    # First fetch.
    filefetcher.fetch(url, store)

    # Second fetch, without the marker file.
    (repository / "marker").unlink()
    path = filefetcher.fetch(url, store)

    # Check that the marker file is gone.
    assert not (path / "marker").is_file()


def test_file_update(repository: Path, store: Store) -> None:
    """It removes files from a previous fetch."""
    repository /= "marker"
    url = asurl(repository)

    # First fetch.
    filefetcher.fetch(url, store)

    # Second fetch, with modified marker file.
    repository.write_text("Ipsum")
    path = filefetcher.fetch(url, store)

    # Check that the marker file is updated.
    assert path.read_text() == "Ipsum"


def test_fetch_error(store: Store) -> None:
    """It raises an exception."""
    url = URL("file:///no/such/file")
    with pytest.raises(CuttyError):
        filefetcher.fetch(url, store)
