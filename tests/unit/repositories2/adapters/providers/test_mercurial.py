"""Unit tests for cutty.repositories2.adapters.providers.mercurial."""
import pathlib
import shutil
import subprocess  # noqa: S404
from typing import Optional
from typing import Protocol

import pytest
from yarl import URL

from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories2.adapters.providers.mercurial import hgproviderfactory
from cutty.repositories2.domain.fetchers import FetchMode
from cutty.repositories2.domain.providers import ProviderStore
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

    hg("init", cwd=path)

    marker = path / "marker"
    marker.write_text("Lorem")

    hg("add", "marker", cwd=path)
    hg("commit", "--message=Initial", cwd=path)

    hg("tag", "--message=Release v1.0", "v1.0", cwd=path)

    marker.write_text("Ipsum")

    hg("add", "marker", cwd=path)
    hg("commit", "--message=Update marker", cwd=path)

    return asurl(path)


@pytest.mark.parametrize(("revision", "expected"), [("v1.0", "Lorem"), (None, "Ipsum")])
def test_hgproviderfactory_happy(
    store: ProviderStore, url: URL, revision: Optional[str], expected: str
):
    """It fetches a hg repository into storage."""
    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    filesystem = hgprovider(url, revision=revision)
    text = filesystem.read_text(PurePath("marker"))
    assert text == expected


def test_hgproviderfactory_not_matching(store: ProviderStore):
    """It returns None if the URL scheme is not recognized."""
    url = URL("mailto:you@example.com")
    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    filesystem = hgprovider(url, revision=None)
    assert filesystem is None
