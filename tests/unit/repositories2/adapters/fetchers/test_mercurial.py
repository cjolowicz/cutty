"""Unit tests for cutty.repositories2.adapters.fetchers.hg."""
import pathlib
import shutil
import subprocess  # noqa: S404
from typing import Optional
from typing import Protocol

import pytest
from yarl import URL

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories2.adapters.fetchers.mercurial import hgfetcher
from cutty.repositories2.domain.fetchers import FetchMode
from cutty.repositories2.domain.stores import Store
from cutty.repositories2.domain.urls import aspath
from cutty.repositories2.domain.urls import asurl


class Hg(Protocol):
    """Protocol for the hg command."""

    def __call__(
        self, *args: str, cwd: Optional[pathlib.Path] = None
    ) -> subprocess.CompletedProcess[str]:
        """Invoke hg."""


@pytest.fixture
def hg() -> Optional[Hg]:
    """Fixture for a hg command."""
    executable = shutil.which("hg")

    def hg(
        *args: str, cwd: Optional[pathlib.Path] = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a hg command."""
        if executable is None:
            pytest.skip("cannot locate hg")

        return subprocess.run(  # noqa: S603
            [executable, *args], check=True, capture_output=True, text=True, cwd=cwd
        )

    return hg


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


defaults = dict(revision=None, mode=FetchMode.ALWAYS)


def test_hgfetcher_happy(url: URL, store: Store):
    """It clones the Mercurial repository."""
    destination = hgfetcher(url, store, **defaults)
    path = Path("marker", filesystem=DiskFilesystem(destination))
    text = path.read_text()
    assert text == "Lorem"


def test_hgfetcher_not_matched(store: Store):
    """It returns None if the URL does not use a recognized scheme."""
    url = URL("mailto:you@example.com")
    path = hgfetcher(url, store, **defaults)
    assert path is None


def test_hgfetcher_no_executable(
    url: URL, store: Store, monkeypatch: pytest.MonkeyPatch
):
    """It raises an exception if the hg executable cannot be located."""
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(Exception):
        hgfetcher(url, store, **defaults)


def test_hgfetcher_update(url: URL, hg: Hg, store: Store):
    """It updates the repository from a previous fetch."""
    # First fetch.
    hgfetcher(url, store, **defaults)

    # Remove the marker file.
    hg("rm", "marker", cwd=aspath(url))
    hg("commit", "--message=Remove the marker file", cwd=aspath(url))

    # Second fetch.
    destination = hgfetcher(url, store, **defaults)

    # Check that the marker file is gone.
    path = Path("marker", filesystem=DiskFilesystem(destination))
    assert not (path / "marker").is_file()
