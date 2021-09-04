"""Unit tests for cutty.repositories.adapters.fetchers.hg."""
import pathlib

import pytest
from yarl import URL

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories.adapters.fetchers.mercurial import Hg
from cutty.repositories.adapters.fetchers.mercurial import HgError
from cutty.repositories.adapters.fetchers.mercurial import hgfetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import aspath
from cutty.repositories.domain.locations import asurl
from cutty.repositories.domain.stores import Store


pytest_plugins = ["tests.fixtures.repositories.adapters.mercurial"]


@pytest.fixture
def url(hg: Hg, tmp_path: pathlib.Path) -> URL:
    """Fixture for a repository."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").write_text("Lorem")

    hg("init", cwd=path)
    hg("add", "marker", cwd=path)
    hg("commit", "--message=Initial", cwd=path)

    return asurl(path)


def test_hgfetcher_happy(url: URL, store: Store) -> None:
    """It clones the Mercurial repository."""
    destination = hgfetcher(url, store, None, FetchMode.ALWAYS)
    assert destination is not None

    path = Path("marker", filesystem=DiskFilesystem(destination))
    assert path.read_text() == "Lorem"


def test_hgfetcher_not_matched(store: Store) -> None:
    """It returns None if the URL does not use a recognized scheme."""
    url = URL("mailto:you@example.com")
    path = hgfetcher(url, store, None, FetchMode.ALWAYS)
    assert path is None


def test_hgfetcher_no_executable(
    url: URL, store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """It raises an exception if the hg executable cannot be located."""
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(Exception):
        hgfetcher(url, store, None, FetchMode.ALWAYS)


def test_hgfetcher_update(url: URL, hg: Hg, store: Store) -> None:
    """It updates the repository from a previous fetch."""
    # First fetch.
    hgfetcher(url, store, None, FetchMode.ALWAYS)

    # Remove the marker file.
    hg("rm", "marker", cwd=aspath(url))
    hg("commit", "--message=Remove the marker file", cwd=aspath(url))

    # Second fetch.
    destination = hgfetcher(url, store, None, FetchMode.ALWAYS)
    assert destination is not None

    # Check that the marker file is gone.
    path = Path("marker", filesystem=DiskFilesystem(destination))
    assert not (path / "marker").is_file()


@pytest.mark.parametrize(
    "url",
    [
        URL("https://example.invalid/repository.git"),
    ],
)
def test_fetch_error(url: URL, store: Store) -> None:
    """It raises an exception with hg's error message."""
    with pytest.raises(HgError):
        hgfetcher(url, store, None, FetchMode.ALWAYS)
