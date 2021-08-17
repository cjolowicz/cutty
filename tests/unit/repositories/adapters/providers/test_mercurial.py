"""Unit tests for cutty.repositories.adapters.providers.mercurial."""
import pathlib
import shutil
import string
import subprocess  # noqa: S404
from typing import Optional
from typing import Protocol

import pytest
from yarl import URL

from cutty.repositories.adapters.providers.mercurial import hgproviderfactory
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import asurl
from cutty.repositories.domain.stores import Store


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
    store: Store, url: URL, revision: Optional[str], expected: str
) -> None:
    """It fetches a hg repository into storage."""
    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    repository = hgprovider(url, revision)
    assert repository is not None

    text = (repository.path / "marker").read_text()
    assert text == expected


def test_hgproviderfactory_revision_commit(store: Store, url: URL) -> None:
    """It returns the short changeset identification hash."""
    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    repository = hgprovider(url, None)
    assert (
        repository is not None
        and repository.revision is not None
        and len(repository.revision) == 12
        and all(c in string.hexdigits for c in repository.revision)
    )


def test_hgproviderfactory_revision_tag(store: Store, url: URL) -> None:
    """It returns the short changeset identification hash."""
    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    repository = hgprovider(url, "tip~2")
    assert repository is not None and repository.revision == "v1.0"


def test_hgproviderfactory_not_matching(store: Store) -> None:
    """It returns None if the URL scheme is not recognized."""
    url = URL("mailto:you@example.com")
    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    repository = hgprovider(url, None)
    assert repository is None
