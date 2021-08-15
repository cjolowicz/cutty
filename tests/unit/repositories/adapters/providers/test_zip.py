"""Unit tests for cutty.repositories.adapters.providers.zip."""
import shutil
from pathlib import Path

import pytest
from yarl import URL

from cutty.repositories.adapters.providers.zip import localzipprovider
from cutty.repositories.adapters.providers.zip import zipproviderfactory
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import asurl
from cutty.repositories.domain.stores import Store


@pytest.fixture
def url(tmp_path: Path) -> URL:
    """Fixture for a repository."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").write_text("Lorem")

    shutil.make_archive(str(path), "zip", str(path))

    archive = path.with_suffix(".zip")
    return asurl(archive)


def test_localzipprovider_happy(url: URL) -> None:
    """It provides a repository from a local directory."""
    repository = localzipprovider(url, None)
    assert repository is not None

    text = (repository.path / "marker").read_text()
    assert text == "Lorem"


def test_localzipprovider_revision(url: URL) -> None:
    """It raises an exception when passed a revision."""
    with pytest.raises(Exception):
        localzipprovider(url, "v1.0")


def test_localzipprovider_not_matching(tmp_path: Path) -> None:
    """It returns None if the path is not a zip repository."""
    url = asurl(tmp_path)
    repository = localzipprovider(url, None)
    assert repository is None


def test_zipproviderfactory_happy(store: Store, url: URL) -> None:
    """It fetches a zip repository into storage."""
    zipprovider = zipproviderfactory(store, FetchMode.ALWAYS)
    repository = zipprovider(url, None)
    assert repository is not None

    text = (repository.path / "marker").read_text()
    assert text == "Lorem"


def test_zipproviderfactory_not_matching(store: Store) -> None:
    """It returns None if the URL scheme is not recognized."""
    url = URL("mailto:you@example.com")
    zipprovider = zipproviderfactory(store, FetchMode.ALWAYS)
    repository = zipprovider(url, None)
    assert repository is None
