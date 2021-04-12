"""Unit tests for cutty.repositories2.adapters.providers.zip."""
import shutil
from pathlib import Path

import pytest
from yarl import URL

from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories2.adapters.providers.zip import localzipprovider
from cutty.repositories2.adapters.providers.zip import zipproviderfactory
from cutty.repositories2.domain.fetchers import FetchMode
from cutty.repositories2.domain.providers import ProviderStore
from cutty.repositories2.domain.urls import asurl


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
    filesystem = localzipprovider(url, revision=None)
    text = filesystem.read_text(PurePath("marker"))
    assert text == "Lorem"


def test_localzipprovider_revision(url: URL) -> None:
    """It raises an exception when passed a revision."""
    with pytest.raises(Exception):
        localzipprovider(url, revision="v1.0")


def test_localzipprovider_not_matching(tmp_path: Path) -> None:
    """It returns None if the path is not a zip repository."""
    url = asurl(tmp_path)
    filesystem = localzipprovider(url, revision=None)
    assert filesystem is None


def test_zipproviderfactory_happy(store: ProviderStore, url: URL) -> None:
    """It fetches a zip repository into storage."""
    zipprovider = zipproviderfactory(store, FetchMode.ALWAYS)
    filesystem = zipprovider(url, revision=None)
    text = filesystem.read_text(PurePath("marker"))
    assert text == "Lorem"


def test_zipproviderfactory_not_matching(store: ProviderStore) -> None:
    """It returns None if the URL scheme is not recognized."""
    url = URL("mailto:you@example.com")
    zipprovider = zipproviderfactory(store, FetchMode.ALWAYS)
    filesystem = zipprovider(url, revision=None)
    assert filesystem is None
