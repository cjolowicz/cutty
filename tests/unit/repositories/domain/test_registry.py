"""Unit tests for cutty.repositories.domain.registry."""
import pathlib

import pytest
from yarl import URL

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.mounters import Mounter
from cutty.repositories.domain.providers import constproviderfactory
from cutty.repositories.domain.providers import LocalProvider
from cutty.repositories.domain.providers import ProviderStore
from cutty.repositories.domain.providers import remoteproviderfactory
from cutty.repositories.domain.registry import ProviderRegistry
from cutty.repositories.domain.repository import Repository
from tests.fixtures.repositories.domain.providers import constprovider
from tests.fixtures.repositories.domain.providers import nullprovider


pytest_plugins = [
    "tests.fixtures.repositories.domain.fetchers",
    "tests.fixtures.repositories.domain.mounters",
    "tests.fixtures.repositories.domain.stores",
]


def test_repositoryprovider_none(providerstore: ProviderStore, url: URL) -> None:
    """It raises an exception if the registry is empty."""
    registry = ProviderRegistry(providerstore, factories=[])
    with pytest.raises(Exception):
        registry(str(url))


def test_repositoryprovider_with_url(
    providerstore: ProviderStore, emptyfetcher: Fetcher, url: URL
) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = remoteproviderfactory("default", fetch=[emptyfetcher])
    registry = ProviderRegistry(providerstore, factories=[providerfactory])
    repository = registry(str(url))
    assert not list(repository.path.iterdir())


def test_repositoryprovider_with_path(
    tmp_path: pathlib.Path,
    providerstore: ProviderStore,
    diskmounter: Mounter,
) -> None:
    """It returns a provider that allows traversing repositories."""
    directory = tmp_path / "repository"
    directory.mkdir()
    (directory / "marker").touch()

    providerfactory = constproviderfactory(
        LocalProvider("default", match=lambda path: True, mount=diskmounter)
    )

    registry = ProviderRegistry(providerstore, factories=[providerfactory])
    repository = registry(str(directory))
    [entry] = repository.path.iterdir()

    assert entry.name == "marker"


def test_repositoryprovider_with_provider_specific_url(
    providerstore: ProviderStore, emptyfetcher: Fetcher, url: URL
) -> None:
    """It selects the provider indicated by the URL scheme."""
    url = url.with_scheme(f"null+{url.scheme}")
    factories = [
        remoteproviderfactory("default", fetch=[emptyfetcher]),
        constproviderfactory(nullprovider),
    ]
    registry = ProviderRegistry(providerstore, factories)
    with pytest.raises(Exception):
        registry(str(url))


def test_repositoryprovider_unknown_provider_in_url_scheme(
    providerstore: ProviderStore, url: URL
) -> None:
    """It invokes providers with the original scheme."""
    repositorypath = Path(filesystem=DictFilesystem({}))
    repository = Repository("example", repositorypath, None)

    factories = [constproviderfactory(constprovider("default", repository))]
    registry = ProviderRegistry(providerstore, factories)
    url = url.with_scheme(f"invalid+{url.scheme}")

    assert repository == registry(str(url))


def test_repositoryprovider_name_from_url(
    providerstore: ProviderStore, emptyfetcher: Fetcher
) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = remoteproviderfactory("default", fetch=[emptyfetcher])
    registry = ProviderRegistry(providerstore, factories=[providerfactory])
    repository = registry("https://example.com/path/to/example?query#fragment")
    assert "example" == repository.name
