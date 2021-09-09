"""Unit tests for cutty.repositories.domain.registry."""
import pathlib

import pytest
from yarl import URL

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.mounters import Mounter
from cutty.repositories.domain.providers import ConstProviderFactory
from cutty.repositories.domain.providers import LocalProvider
from cutty.repositories.domain.providers import Provider
from cutty.repositories.domain.providers import ProviderStore
from cutty.repositories.domain.providers import RemoteProviderFactory
from cutty.repositories.domain.registry import provide
from cutty.repositories.domain.registry import ProviderRegistry
from cutty.repositories.domain.repository import Repository
from tests.fixtures.repositories.domain.providers import constprovider
from tests.fixtures.repositories.domain.providers import dictprovider
from tests.fixtures.repositories.domain.providers import nullprovider


pytest_plugins = [
    "tests.fixtures.repositories.domain.fetchers",
    "tests.fixtures.repositories.domain.mounters",
    "tests.fixtures.repositories.domain.stores",
]


@pytest.mark.parametrize(
    "providers",
    [
        [],
        [nullprovider],
        [nullprovider, nullprovider],
    ],
)
def test_provide_fail(providers: list[Provider]) -> None:
    """It raises an exception."""
    with pytest.raises(Exception):
        provide(providers, URL())


@pytest.mark.parametrize(
    "providers",
    [
        [dictprovider({})],
        [dictprovider({}), nullprovider],
        [nullprovider, dictprovider({})],
        [dictprovider({}), dictprovider({"marker": ""})],
    ],
)
def test_provide_pass(providers: list[Provider]) -> None:
    """It returns a path to the filesystem."""
    repository = provide(providers, URL())
    assert repository.path.is_dir()
    assert not (repository.path / "marker").is_file()


def test_none(providerstore: ProviderStore, url: URL) -> None:
    """It raises an exception if the registry is empty."""
    registry = ProviderRegistry(providerstore, factories=[])
    with pytest.raises(Exception):
        registry(str(url))


def test_with_url(
    providerstore: ProviderStore, emptyfetcher: Fetcher, url: URL
) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = RemoteProviderFactory("default", fetch=[emptyfetcher])
    registry = ProviderRegistry(providerstore, [providerfactory])
    repository = registry(str(url))
    assert not list(repository.path.iterdir())


def test_with_path(
    tmp_path: pathlib.Path,
    providerstore: ProviderStore,
    diskmounter: Mounter,
) -> None:
    """It returns a provider that allows traversing repositories."""
    directory = tmp_path / "repository"
    directory.mkdir()
    (directory / "marker").touch()

    providerfactory = ConstProviderFactory(
        LocalProvider("default", match=lambda path: True, mount=diskmounter)
    )

    registry = ProviderRegistry(providerstore, [providerfactory])
    repository = registry(str(directory))
    [entry] = repository.path.iterdir()

    assert entry.name == "marker"


def test_with_provider_specific_url(
    providerstore: ProviderStore, emptyfetcher: Fetcher, url: URL
) -> None:
    """It selects the provider indicated by the URL scheme."""
    url = url.with_scheme(f"null+{url.scheme}")
    factories = [
        RemoteProviderFactory("default", fetch=[emptyfetcher]),
        ConstProviderFactory(nullprovider),
    ]
    registry = ProviderRegistry(providerstore, factories)
    with pytest.raises(Exception):
        registry(str(url))


def test_unknown_provider_in_url_scheme(providerstore: ProviderStore, url: URL) -> None:
    """It invokes providers with the original scheme."""
    repositorypath = Path(filesystem=DictFilesystem({}))
    repository = Repository("example", repositorypath, None)

    factories = [ConstProviderFactory(constprovider("default", repository))]
    registry = ProviderRegistry(providerstore, factories)
    url = url.with_scheme(f"invalid+{url.scheme}")

    assert repository == registry(str(url))


def test_provider_specific_file_url(providerstore: ProviderStore) -> None:
    """It does not crash when rewriting provider-specific file:// URLs."""
    # https://github.com/aio-libs/yarl/issues/280
    registry = ProviderRegistry(providerstore, [ConstProviderFactory(dictprovider())])
    registry("dict+file:///path/to/repository.zip")  # does not raise


def test_name_from_url(providerstore: ProviderStore, emptyfetcher: Fetcher) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = RemoteProviderFactory("default", fetch=[emptyfetcher])
    registry = ProviderRegistry(providerstore, [providerfactory])
    repository = registry("https://example.com/path/to/example?query#fragment")
    assert "example" == repository.name
