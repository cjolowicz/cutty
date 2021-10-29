"""Unit tests for cutty.packages.domain.registry."""
import pathlib

import pytest
from yarl import URL

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.packages.domain.fetchers import Fetcher
from cutty.packages.domain.mounters import Mounter
from cutty.packages.domain.package import Package
from cutty.packages.domain.providers import ConstProviderFactory
from cutty.packages.domain.providers import LocalProvider
from cutty.packages.domain.providers import Provider
from cutty.packages.domain.providers import RemoteProviderFactory
from cutty.packages.domain.registry import ProviderRegistry
from cutty.packages.domain.registry import ProviderStore
from tests.fixtures.packages.domain.providers import constprovider
from tests.fixtures.packages.domain.providers import dictprovider
from tests.fixtures.packages.domain.providers import nullprovider


pytest_plugins = [
    "tests.fixtures.packages.domain.fetchers",
    "tests.fixtures.packages.domain.mounters",
    "tests.fixtures.packages.domain.stores",
]


@pytest.mark.parametrize(
    "providers",
    [
        [],
        [nullprovider],
        [nullprovider, Provider("null2")],
    ],
)
def test_provide_fail(providerstore: ProviderStore, providers: list[Provider]) -> None:
    """It raises an exception."""
    registry = ProviderRegistry(
        providerstore,
        factories=[ConstProviderFactory(provider) for provider in providers],
    )

    with pytest.raises(Exception):
        registry.getrepository("")


@pytest.mark.parametrize(
    "providers",
    [
        [dictprovider({})],
        [dictprovider({}), nullprovider],
        [nullprovider, dictprovider({})],
        [dictprovider({}), dictprovider({"marker": ""}, name="dict2")],
    ],
)
def test_provide_pass(providerstore: ProviderStore, providers: list[Provider]) -> None:
    """It returns a path to the filesystem."""
    registry = ProviderRegistry(
        providerstore,
        factories=[ConstProviderFactory(provider) for provider in providers],
    )

    repository = registry.getrepository("")
    with repository.get() as package:
        assert package.tree.is_dir()
        assert not (package.tree / "marker").is_file()


def test_none(providerstore: ProviderStore, url: URL) -> None:
    """It raises an exception if the registry is empty."""
    registry = ProviderRegistry(providerstore, factories=[])
    with pytest.raises(Exception):
        registry.getrepository(str(url))


def test_with_url(
    providerstore: ProviderStore, emptyfetcher: Fetcher, url: URL
) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = RemoteProviderFactory("default", fetch=[emptyfetcher])
    registry = ProviderRegistry(providerstore, [providerfactory])
    repository = registry.getrepository(str(url))

    with repository.get() as package:
        assert not list(package.tree.iterdir())


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
    repository = registry.getrepository(str(directory))

    with repository.get() as package:
        [entry] = package.tree.iterdir()

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
        registry.getrepository(str(url))


def test_unknown_provider_in_url_scheme(providerstore: ProviderStore, url: URL) -> None:
    """It invokes providers with the original scheme."""
    packagepath = Path(filesystem=DictFilesystem({}))
    package = Package("example", packagepath, None)

    factories = [ConstProviderFactory(constprovider("default", package))]
    registry = ProviderRegistry(providerstore, factories)
    url = url.with_scheme(f"invalid+{url.scheme}")
    repository = registry.getrepository(str(url))

    with repository.get() as package2:
        assert package == package2


def test_provider_specific_file_url(providerstore: ProviderStore) -> None:
    """It does not crash when rewriting provider-specific file:// URLs."""
    # https://github.com/aio-libs/yarl/issues/280
    registry = ProviderRegistry(providerstore, [ConstProviderFactory(dictprovider())])
    registry.getrepository("dict+file:///path/to/repository.zip")  # does not raise


def test_name_from_url(providerstore: ProviderStore, emptyfetcher: Fetcher) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = RemoteProviderFactory("default", fetch=[emptyfetcher])
    registry = ProviderRegistry(providerstore, [providerfactory])
    repository = registry.getrepository(
        "https://example.com/path/to/example?query#fragment"
    )

    with repository.get() as package:
        assert "example" == package.name
