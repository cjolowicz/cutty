"""Unit tests for cutty.packages.domain.providers."""
import json
import pathlib
from typing import Optional

import pytest
from yarl import URL

from cutty.packages.domain.fetchers import Fetcher
from cutty.packages.domain.locations import asurl
from cutty.packages.domain.matchers import Matcher
from cutty.packages.domain.mounters import Mounter
from cutty.packages.domain.providers import LocalProvider
from cutty.packages.domain.providers import RemoteProviderFactory
from cutty.packages.domain.revisions import Revision
from cutty.packages.domain.stores import Store


pytest_plugins = [
    "tests.fixtures.packages.domain.fetchers",
    "tests.fixtures.packages.domain.matchers",
    "tests.fixtures.packages.domain.mounters",
]


def test_localprovider_not_local(url: URL, diskmounter: Mounter) -> None:
    """It returns None if the location is not local."""
    provider = LocalProvider(match=lambda path: True, mount=diskmounter)

    assert provider.provide(url) is None


def test_localprovider_not_matching(
    tmp_path: pathlib.Path, diskmounter: Mounter
) -> None:
    """It returns None if the provider does not match."""
    url = asurl(tmp_path)
    provider = LocalProvider(match=lambda path: False, mount=diskmounter)

    assert provider.provide(url) is None


def test_localprovider_inexistent_path(diskmounter: Mounter) -> None:
    """It returns None if the location is an inexistent path."""
    provider = LocalProvider(match=lambda path: True, mount=diskmounter)
    path = pathlib.Path("/no/such/file/or/directory")

    assert provider.provide(path) is None


def test_localprovider_path(tmp_path: pathlib.Path, diskmounter: Mounter) -> None:
    """It returns the package repository."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").touch()

    url = asurl(path)
    provider = LocalProvider(match=lambda path: True, mount=diskmounter)
    repository = provider.provide(url)

    assert repository is not None

    with repository.get() as package:
        [entry] = package.path.iterdir()
        assert entry.name == "marker"


def test_localprovider_revision(tmp_path: pathlib.Path, diskmounter: Mounter) -> None:
    """It raises an exception if the mounter does not support revisions."""
    url = asurl(tmp_path)
    provider = LocalProvider(match=lambda path: True, mount=diskmounter)

    with pytest.raises(Exception):
        if repository := provider.provide(url):
            with repository.get("v1.0.0"):
                pass


def test_localprovider_package_revision(
    tmp_path: pathlib.Path, diskmounter: Mounter
) -> None:
    """It determines the revision of the package."""

    def getrevision(
        path: pathlib.Path, revision: Optional[Revision]
    ) -> Optional[Revision]:
        """Return the contents of the VERSION file."""
        return (path / "VERSION").read_text().strip()

    provider = LocalProvider(
        match=lambda _: True, mount=diskmounter, getrevision=getrevision
    )

    path = tmp_path / "repository"
    path.mkdir()
    (path / "VERSION").write_text("1.0")

    repository = provider.provide(asurl(path))

    assert repository is not None

    with repository.get() as package:
        assert "1.0" == package.revision


def test_remoteproviderfactory_no_fetchers(store: Store) -> None:
    """It returns None if there are no fetchers."""
    providerfactory = RemoteProviderFactory(fetch=[])
    provider = providerfactory(store)
    assert provider.provide(URL()) is None


def test_remoteproviderfactory_no_matching_fetchers(
    store: Store, nullfetcher: Fetcher
) -> None:
    """It returns None if all fetchers return None."""
    providerfactory = RemoteProviderFactory(fetch=[nullfetcher])
    provider = providerfactory(store)
    assert provider.provide(URL()) is None


def test_remoteproviderfactory_happy(
    store: Store, emptyfetcher: Fetcher, url: URL
) -> None:
    """It mounts a filesystem for the fetched package."""
    providerfactory = RemoteProviderFactory(fetch=[emptyfetcher])
    provider = providerfactory(store)
    repository = provider.provide(url)

    assert repository is not None


def test_remoteproviderfactory_package_revision(
    store: Store, emptyfetcher: Fetcher, url: URL
) -> None:
    """It returns the package revision."""

    def getrevision(
        path: pathlib.Path, revision: Optional[Revision]
    ) -> Optional[Revision]:
        """Return a fake version."""
        return "v1.0"

    providerfactory = RemoteProviderFactory(
        fetch=[emptyfetcher], getrevision=getrevision
    )
    provider = providerfactory(store)
    repository = provider.provide(url)

    assert repository is not None

    with repository.get() as package:
        assert package.revision == "v1.0"


def test_remoteproviderfactory_not_matching(
    store: Store, emptyfetcher: Fetcher, url: URL, nullmatcher: Matcher
) -> None:
    """It returns None if the provider itself does not match."""
    providerfactory = RemoteProviderFactory(match=nullmatcher, fetch=[emptyfetcher])
    provider = providerfactory(store)
    assert provider.provide(url) is None


def test_remoteproviderfactory_mounter(
    store: Store, emptyfetcher: Fetcher, url: URL, jsonmounter2: Mounter
) -> None:
    """It uses the mounter to mount the filesystem."""
    url = url.with_name(f"{url.name}.json")
    revision = "v1.0.0"
    if path := emptyfetcher(url, store):
        text = json.dumps({revision: {"marker": "Lorem"}})
        path.write_text(text)

    providerfactory = RemoteProviderFactory(fetch=[emptyfetcher], mount=jsonmounter2)
    provider = providerfactory(store)
    repository = provider.provide(url)

    assert repository is not None

    with repository.get(revision) as package:
        assert (package.path / "marker").read_text() == "Lorem"


def test_remoteproviderfactory_inexistent_path(
    store: Store, emptyfetcher: Fetcher, nullmatcher: Matcher
) -> None:
    """It returns None if the location is an inexistent path."""
    providerfactory = RemoteProviderFactory(fetch=[emptyfetcher])
    provider = providerfactory(store)
    path = pathlib.Path("/no/such/file/or/directory")

    assert provider.provide(path) is None
