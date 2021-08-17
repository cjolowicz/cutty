"""Unit tests for cutty.repositories.adapters.providers.mercurial."""
import pathlib
import string
import subprocess  # noqa: S404
from typing import Optional

import pytest
from yarl import URL

from cutty.repositories.adapters.fetchers.mercurial import findhg
from cutty.repositories.adapters.fetchers.mercurial import Hg
from cutty.repositories.adapters.providers.mercurial import hgproviderfactory
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.stores import Store


@pytest.fixture
def hg() -> Hg:
    """Fixture for a hg command."""
    hg = findhg()

    def _hg(
        *args: str, cwd: Optional[pathlib.Path] = None
    ) -> subprocess.CompletedProcess[str]:
        try:
            return hg(*args, cwd=cwd)
        except RuntimeError:
            pytest.skip("cannot locate hg")

    return _hg


@pytest.fixture
def hgrepository(hg: Hg, tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture for a Mercurial repository."""
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

    return path


@pytest.mark.parametrize(("revision", "expected"), [("v1.0", "Lorem"), (None, "Ipsum")])
def test_hgproviderfactory_happy(
    store: Store, hgrepository: pathlib.Path, revision: Optional[str], expected: str
) -> None:
    """It fetches a hg repository into storage."""
    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    repository = hgprovider(hgrepository, revision)
    assert repository is not None

    text = (repository.path / "marker").read_text()
    assert text == expected


def test_hgproviderfactory_revision_commit(
    store: Store, hgrepository: pathlib.Path
) -> None:
    """It returns the short changeset identification hash."""
    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    repository = hgprovider(hgrepository, None)
    assert (
        repository is not None
        and repository.revision is not None
        and len(repository.revision) == 12
        and all(c in string.hexdigits for c in repository.revision)
    )


def test_hgproviderfactory_revision_tag(
    store: Store, hgrepository: pathlib.Path
) -> None:
    """It returns the short changeset identification hash."""
    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    repository = hgprovider(hgrepository, "tip~2")
    assert repository is not None and repository.revision == "v1.0"


def test_hgproviderfactory_revision_no_tags(
    store: Store, hg: Hg, tmp_path: pathlib.Path
) -> None:
    """It returns the changeset hash in a repository without tags."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").touch()

    hg("init", cwd=path)
    hg("add", "marker", cwd=path)
    hg("commit", "--message=Initial", cwd=path)

    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    repository = hgprovider(path, None)
    assert (
        repository is not None
        and repository.revision is not None
        and len(repository.revision) == 12
        and all(c in string.hexdigits for c in repository.revision)
    )


def test_hgproviderfactory_revision_multiple_tags(
    store: Store, hg: Hg, tmp_path: pathlib.Path
) -> None:
    """It returns the tag names separated by colon."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").touch()

    hg("init", cwd=path)
    hg("add", "marker", cwd=path)
    hg("commit", "--message=Initial", cwd=path)
    hg("tag", "--rev=0", "tag1", cwd=path)
    hg("tag", "--rev=0", "tag2", cwd=path)

    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    repository = hgprovider(path, "tip~2")
    assert repository is not None and repository.revision == "tag1:tag2"


def test_hgproviderfactory_not_matching(store: Store) -> None:
    """It returns None if the URL scheme is not recognized."""
    url = URL("mailto:you@example.com")
    hgprovider = hgproviderfactory(store, FetchMode.ALWAYS)
    repository = hgprovider(url, None)
    assert repository is None
