"""Unit tests for cutty.packages.adapters.providers.zip."""
import shutil
from pathlib import Path

import pytest
from yarl import URL

from cutty.packages.adapters.providers.zip import localzipprovider
from cutty.packages.adapters.providers.zip import zipproviderfactory
from cutty.packages.domain.locations import asurl
from cutty.packages.domain.stores import Store


@pytest.fixture
def url(tmp_path: Path) -> URL:
    """Fixture for a package."""
    path = tmp_path / "package"
    path.mkdir()
    (path / "marker").write_text("Lorem")

    shutil.make_archive(str(path), "zip", str(path))

    archive = path.with_suffix(".zip")
    return asurl(archive)


def test_local_happy(url: URL) -> None:
    """It provides a package from a local directory."""
    repository = localzipprovider.provide(url)

    assert repository is not None

    with repository.get() as package:
        text = (package.path / "marker").read_text()
        assert text == "Lorem"


def test_local_revision(url: URL) -> None:
    """It raises an exception when passed a revision."""
    with pytest.raises(Exception):
        localzipprovider.provide(url, "v1.0")


def test_local_not_matching(tmp_path: Path) -> None:
    """It returns None if the path is not a zip package."""
    repository = localzipprovider.provide(asurl(tmp_path))

    assert repository is None


def test_remote_happy(store: Store, url: URL) -> None:
    """It fetches a zip package into storage."""
    zipprovider = zipproviderfactory(store)
    repository = zipprovider.provide(url)

    assert repository is not None

    with repository.get() as package:
        text = (package.path / "marker").read_text()
        assert text == "Lorem"


def test_remote_not_matching(store: Store) -> None:
    """It returns None if the URL scheme is not recognized."""
    zipprovider = zipproviderfactory(store)
    repository = zipprovider.provide(URL("mailto:you@example.com"))

    assert repository is None
