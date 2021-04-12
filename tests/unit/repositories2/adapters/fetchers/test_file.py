"""Unit tests for cutty.repositories2.adapters.fetchers.file."""
from pathlib import Path

import pytest
from yarl import URL

from cutty.repositories2.adapters.fetchers.file import filefetcher
from cutty.repositories2.domain.fetchers import FetchMode
from cutty.repositories2.domain.stores import Store
from cutty.repositories2.domain.urls import asurl


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").write_text("Lorem")
    return path


def test_filefetcher_directory_happy(repository: Path, store: Store) -> None:
    """It copies the filesystem tree."""
    url = asurl(repository)
    path = filefetcher(url, store, None, FetchMode.ALWAYS)

    assert path is not None
    assert (path / "marker").read_text() == "Lorem"


def test_filefetcher_file_happy(repository: Path, store: Store) -> None:
    """It copies the file."""
    repository /= "marker"
    url = asurl(repository)
    path = filefetcher(url, store, None, FetchMode.ALWAYS)

    assert path is not None
    assert path.read_text() == "Lorem"


def test_filefetcher_not_matched(store: Store, url: URL) -> None:
    """It returns None if the URL does not use the file scheme."""
    path = filefetcher(url, store, None, FetchMode.ALWAYS)
    assert path is None


def test_filefetcher_directory_update(repository: Path, store: Store) -> None:
    """It removes files from a previous fetch."""
    url = asurl(repository)

    # First fetch.
    filefetcher(url, store, None, FetchMode.ALWAYS)

    # Second fetch, without the marker file.
    (repository / "marker").unlink()
    path = filefetcher(url, store, None, FetchMode.ALWAYS)

    # Check that the marker file is gone.
    assert path is not None
    assert not (path / "marker").is_file()


def test_filefetcher_file_update(repository: Path, store: Store) -> None:
    """It removes files from a previous fetch."""
    repository /= "marker"
    url = asurl(repository)

    # First fetch.
    filefetcher(url, store, None, FetchMode.ALWAYS)

    # Second fetch, with modified marker file.
    repository.write_text("Ipsum")
    path = filefetcher(url, store, None, FetchMode.ALWAYS)

    # Check that the marker file is updated.
    assert path is not None
    assert path.read_text() == "Ipsum"
