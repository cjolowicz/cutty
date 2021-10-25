"""Unit tests for cutty.packages.adapters.fetchers.hg."""
import os
import pathlib
import shutil

import httpx
import pytest
from yarl import URL

from cutty.errors import CuttyError
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.path import Path
from cutty.packages.adapters.fetchers.mercurial import Hg
from cutty.packages.adapters.fetchers.mercurial import hgfetcher
from cutty.packages.domain.locations import asurl
from cutty.packages.domain.stores import Store


pytest_plugins = ["tests.fixtures.repositories.adapters.mercurial"]


@pytest.fixture(scope="session")
def sessionrepository(hg: Hg, session_tmp_path: pathlib.Path) -> pathlib.Path:
    """Session fixture for a Mercurial repository."""
    path = session_tmp_path / "sessionrepository"
    path.mkdir()
    (path / "marker").write_text("Lorem")

    hg("init", cwd=path)
    hg("add", "marker", cwd=path)
    hg("commit", "--message=Initial", cwd=path)

    return path


@pytest.fixture
def url(sessionrepository: pathlib.Path) -> URL:
    """Fixture for a Mercurial repository URL."""
    return asurl(sessionrepository)


def test_happy(url: URL, store: Store) -> None:
    """It clones the Mercurial repository."""
    destination = hgfetcher(url, store)
    assert destination is not None

    path = Path("marker", filesystem=DiskFilesystem(destination))
    assert path.read_text() == "Lorem"


def test_not_matched(store: Store) -> None:
    """It returns None if the URL does not use a recognized scheme."""
    url = URL("mailto:you@example.com")
    path = hgfetcher(url, store)
    assert path is None


def test_no_executable(url: URL, store: Store, monkeypatch: pytest.MonkeyPatch) -> None:
    """It raises an exception if the hg executable cannot be located."""
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(Exception):
        hgfetcher(url, store)


@pytest.fixture
def repository(tmp_path: pathlib.Path, sessionrepository: pathlib.Path) -> pathlib.Path:
    """Fixture for a Mercurial repository."""
    path = tmp_path / "repository"
    shutil.copytree(sessionrepository, path)

    return path


def test_update(repository: pathlib.Path, hg: Hg, store: Store) -> None:
    """It updates the repository from a previous fetch."""
    # First fetch.
    hgfetcher(asurl(repository), store)

    # Remove the marker file.
    hg("rm", "marker", cwd=repository)
    hg("commit", "--message=Remove the marker file", cwd=repository)

    # Second fetch.
    destination = hgfetcher(asurl(repository), store)
    assert destination is not None

    # Check that the marker file is gone.
    path = Path("marker", filesystem=DiskFilesystem(destination))
    assert not (path / "marker").is_file()


@pytest.fixture(scope="session")
def skip_on_http_errors() -> None:
    """Skip a test if HTTP requests don't succeed within a configurable timeout."""
    if envvar := os.environ.get("CUTTY_TESTS_HTTP_TIMEOUT"):
        timeout = float(envvar)
    else:
        timeout = 1

    try:
        httpx.get("https://example.com/", timeout=timeout)
    except httpx.HTTPError as error:
        pytest.skip(f"HTTP failure: {error}")


@pytest.mark.parametrize(
    "url",
    [
        URL("https://example.invalid/repository.git"),
        URL("https://example.com/repository.git"),
        URL("https://example.com/index.html"),
    ],
    ids=str,
)
def test_fetch_error(url: URL, hg: Hg, store: Store, skip_on_http_errors: None) -> None:
    """It raises an exception."""
    with pytest.raises(CuttyError):
        hgfetcher(url, store)


def test_revision_not_found(url: URL, hg: Hg, store: Store) -> None:
    """It raises an exception."""
    with pytest.raises(CuttyError):
        hgfetcher(url, store, "invalid")
