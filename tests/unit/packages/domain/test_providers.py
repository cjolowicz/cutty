"""Unit tests for cutty.packages.domain.providers."""
import json
import pathlib

import pytest
from yarl import URL

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.packages.domain.fetchers import Fetcher
from cutty.packages.domain.loader import MountedPackageRepositoryLoader
from cutty.packages.domain.locations import asurl
from cutty.packages.domain.matchers import Matcher
from cutty.packages.domain.mounters import Mounter
from cutty.packages.domain.mounters import unversioned_mounter
from cutty.packages.domain.providers import LocalProvider
from cutty.packages.domain.providers import RemoteProviderFactory
from cutty.packages.domain.stores import Store


pytest_plugins = [
    "tests.fixtures.packages.domain.fetchers",
    "tests.fixtures.packages.domain.matchers",
    "tests.fixtures.packages.domain.mounters",
]


def test_localprovider_not_local(url: URL) -> None:
    """It returns None if the location is not local."""
    provider = LocalProvider(match=lambda path: True)

    assert provider.provide(url) is None


def test_localprovider_not_matching(tmp_path: pathlib.Path) -> None:
    """It returns None if the provider does not match."""
    url = asurl(tmp_path)
    provider = LocalProvider(match=lambda path: False)

    assert provider.provide(url) is None


def test_localprovider_inexistent_path() -> None:
    """It returns None if the location is an inexistent path."""
    provider = LocalProvider(match=lambda path: True)
    path = pathlib.Path("/no/such/file/or/directory")

    assert provider.provide(path) is None


def test_localprovider_path(tmp_path: pathlib.Path) -> None:
    """It returns the package repository."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").touch()

    url = asurl(path)
    provider = LocalProvider(match=lambda path: True)
    repository = provider.provide(url)

    assert repository is not None

    with repository.get() as package:
        [entry] = package.tree.iterdir()
        assert entry.name == "marker"


def test_localprovider_revision(tmp_path: pathlib.Path) -> None:
    """It raises an exception if the mounter does not support revisions."""
    loader = MountedPackageRepositoryLoader(unversioned_mounter(DiskFilesystem))
    provider = LocalProvider(match=lambda path: True, loader=loader)

    with pytest.raises(Exception):
        if repository := provider.provide(tmp_path):
            with repository.get("v1.0.0"):
                pass


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


def test_remoteproviderfactory_not_matching(
    store: Store, emptyfetcher: Fetcher, url: URL, nullmatcher: Matcher
) -> None:
    """It returns None if the provider itself does not match."""
    providerfactory = RemoteProviderFactory(match=nullmatcher, fetch=[emptyfetcher])
    provider = providerfactory(store)
    assert provider.provide(url) is None


def test_remoteproviderfactory_mounter(
    store: Store, emptyfetcher: Fetcher, url: URL, jsonmounter: Mounter
) -> None:
    """It uses the mounter to mount the filesystem."""
    url = url.with_name(f"{url.name}.json")
    revision = "v1.0.0"

    path = emptyfetcher.fetch(url, store)
    text = json.dumps({revision: {"marker": "Lorem"}})
    path.write_text(text)

    providerfactory = RemoteProviderFactory(
        fetch=[emptyfetcher], loader=MountedPackageRepositoryLoader(jsonmounter)
    )
    provider = providerfactory(store)
    repository = provider.provide(url)

    assert repository is not None

    with repository.get(revision) as package:
        assert (package.tree / "marker").read_text() == "Lorem"


def test_remoteproviderfactory_inexistent_path(
    store: Store, emptyfetcher: Fetcher, nullmatcher: Matcher
) -> None:
    """It returns None if the location is an inexistent path."""
    providerfactory = RemoteProviderFactory(fetch=[emptyfetcher])
    provider = providerfactory(store)
    path = pathlib.Path("/no/such/file/or/directory")

    assert provider.provide(path) is None
