"""Unit tests for cutty.repositories.domain.registry."""
import pathlib
from collections.abc import Callable
from typing import Optional

import pytest
from yarl import URL

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import Location
from cutty.repositories.domain.mounters import unversioned_mounter
from cutty.repositories.domain.providers import constproviderfactory
from cutty.repositories.domain.providers import LocalProvider
from cutty.repositories.domain.providers import Provider
from cutty.repositories.domain.providers import ProviderStore
from cutty.repositories.domain.providers import remoteproviderfactory
from cutty.repositories.domain.registry import ProviderRegistry
from cutty.repositories.domain.repository import Repository
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import Store


defaultmount = unversioned_mounter(DiskFilesystem)


ProviderFunction = Callable[[Location, Optional[Revision]], Optional[Repository]]


def provider(function: ProviderFunction) -> Provider:
    """Decorator to create a provider from a function."""

    class _Provider(Provider):
        def __call__(
            self, location: Location, revision: Optional[Revision]
        ) -> Optional[Repository]:
            return function(location, revision)

    return _Provider()


nullprovider = Provider()
"""Provider that matches no location."""


def constprovider(repository: Repository) -> Provider:
    """Provider that returns the same repository always."""

    @provider
    def _constprovider(
        location: Location, revision: Optional[Revision]
    ) -> Optional[Repository]:
        return repository

    return _constprovider


@pytest.fixture
def fetcher() -> Fetcher:
    """Fixture for a fetcher that simply creates the destination path."""

    def _fetcher(
        url: URL, store: Store, revision: Optional[Revision], mode: FetchMode
    ) -> Optional[pathlib.Path]:
        path = store(url) / url.name

        if path.suffix:
            path.touch()
        else:
            path.mkdir(exist_ok=True)

        return path

    return _fetcher


def test_repositoryprovider_none(providerstore: ProviderStore, url: URL) -> None:
    """It raises an exception if the registry is empty."""
    registry = ProviderRegistry({}, providerstore)
    with pytest.raises(Exception):
        registry(str(url))


def test_repositoryprovider_with_url(
    providerstore: ProviderStore, fetcher: Fetcher, url: URL
) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = remoteproviderfactory(fetch=[fetcher])
    registry = ProviderRegistry({"default": providerfactory}, providerstore)
    repository = registry(str(url))
    assert not list(repository.path.iterdir())


def test_repositoryprovider_with_path(
    tmp_path: pathlib.Path, providerstore: ProviderStore, fetcher: Fetcher
) -> None:
    """It returns a provider that allows traversing repositories."""
    directory = tmp_path / "repository"
    directory.mkdir()
    (directory / "marker").touch()

    providerfactory = constproviderfactory(
        LocalProvider(match=lambda path: True, mount=defaultmount)
    )

    registry = ProviderRegistry({"default": providerfactory}, providerstore)
    repository = registry(str(directory))
    [entry] = repository.path.iterdir()

    assert entry.name == "marker"


def test_repositoryprovider_with_provider_specific_url(
    providerstore: ProviderStore, fetcher: Fetcher, url: URL
) -> None:
    """It selects the provider indicated by the URL scheme."""
    url = url.with_scheme(f"null+{url.scheme}")
    factories = {
        "default": remoteproviderfactory(fetch=[fetcher]),
        "null": constproviderfactory(nullprovider),
    }
    registry = ProviderRegistry(factories, providerstore)
    with pytest.raises(Exception):
        registry(str(url))


def test_repositoryprovider_unknown_provider_in_url_scheme(
    providerstore: ProviderStore, url: URL
) -> None:
    """It invokes providers with the original scheme."""
    repositorypath = Path(filesystem=DictFilesystem({}))
    repository = Repository("example", repositorypath, None)

    factories = {"default": constproviderfactory(constprovider(repository))}
    registry = ProviderRegistry(factories, providerstore)
    url = url.with_scheme(f"invalid+{url.scheme}")

    assert repository == registry(str(url))


def test_repositoryprovider_name_from_url(
    providerstore: ProviderStore, fetcher: Fetcher
) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = remoteproviderfactory(fetch=[fetcher])
    registry = ProviderRegistry({"default": providerfactory}, providerstore)
    repository = registry("https://example.com/path/to/example?query#fragment")
    assert "example" == repository.name
