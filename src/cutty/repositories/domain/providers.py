"""Repository providers."""
import pathlib
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional
from typing import Protocol

from yarl import URL

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.pathfs import PathFilesystem
from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import aspath
from cutty.repositories.domain.locations import asurl
from cutty.repositories.domain.locations import Location
from cutty.repositories.domain.locations import parselocation
from cutty.repositories.domain.matchers import Matcher
from cutty.repositories.domain.matchers import PathMatcher
from cutty.repositories.domain.mounters import Mounter
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import Store


@dataclass
class Repository:
    """A repository."""

    name: str
    path: Path
    revision: Optional[Revision]


class RepositoryProvider(Protocol):
    """The repository provider turns a repository URL into a filesystem path."""

    def __call__(
        self,
        location: str,
        revision: Optional[Revision] = None,
        fetchmode: FetchMode = FetchMode.ALWAYS,
        directory: Optional[PurePath] = None,
    ) -> Repository:
        """Return the repository located at the given URL."""


Provider = Callable[[Location, Optional[Revision]], Optional[Filesystem]]
Provider2 = Callable[[Location, Optional[Revision]], Optional[Repository]]


def asprovider2(provider: Provider) -> Provider2:
    """Convert Provider to Provider2."""

    def _provider2(
        location: Location, revision: Optional[Revision]
    ) -> Optional[Repository]:
        filesystem = provider(location, revision)
        if filesystem is not None:
            path = Path(filesystem=filesystem)
            return Repository(location.name, path, revision)
        return None

    return _provider2


def provide(
    providers: Iterable[Provider2], location: Location, revision: Optional[Revision]
) -> Repository:
    """Provide the repository located at the given URL."""
    for provider in providers:
        repository = provider(location, revision)
        if repository is not None:
            return repository

    raise RuntimeError(f"unknown location {location}")


ProviderFactory = Callable[[Store, FetchMode], Provider]
ProviderFactory2 = Callable[[Store, FetchMode], Provider2]


def asproviderfactory2(providerfactory: ProviderFactory) -> ProviderFactory2:
    """Convert ProviderFactory to ProviderFactory2."""

    def _providerfactory2(store: Store, fetchmode: FetchMode) -> Provider2:
        provider = providerfactory(store, fetchmode)
        return asprovider2(provider)

    return _providerfactory2


def localprovider(*, match: PathMatcher, mount: Mounter) -> Provider2:
    """Create a view onto the local filesystem."""

    def _localprovider(
        location: Location, revision: Optional[Revision]
    ) -> Optional[Filesystem]:
        try:
            path = location if isinstance(location, pathlib.Path) else aspath(location)
        except ValueError:
            return None
        else:
            return mount(path, revision) if match(path) else None

    return asprovider2(_localprovider)


def _defaultmount(path: pathlib.Path, revision: Optional[Revision]) -> Filesystem:
    return DiskFilesystem(path)


def remoteproviderfactory(
    *,
    match: Optional[Matcher] = None,
    fetch: Iterable[Fetcher],
    mount: Optional[Mounter] = None,
) -> ProviderFactory:
    """Remote providers fetch the repository into local storage first."""
    fetch = tuple(fetch)
    _mount = mount if mount is not None else _defaultmount

    def _remoteproviderfactory(store: Store, fetchmode: FetchMode) -> Provider:
        def _remoteprovider(
            location: Location, revision: Optional[Revision]
        ) -> Optional[Filesystem]:
            url = location if isinstance(location, URL) else asurl(location)
            if match is None or match(url):
                for fetcher in fetch:
                    path = fetcher(url, store, revision, fetchmode)
                    if path is not None:
                        return _mount(path, revision)

            return None

        return _remoteprovider

    return _remoteproviderfactory


ProviderName = str
ProviderStore = Callable[[ProviderName], Store]
ProviderRegistry = Mapping[ProviderName, ProviderFactory]
ProviderRegistry2 = Mapping[ProviderName, ProviderFactory2]


def asproviderregistry2(providerregistry: ProviderRegistry) -> ProviderRegistry2:
    """Convert ProviderRegistry to ProviderRegistry2."""
    return {
        providername: asproviderfactory2(providerfactory)
        for providername, providerfactory in providerregistry.items()
    }


_emptyproviderregistry: ProviderRegistry2 = MappingProxyType({})


def registerproviderfactories2(
    providerregistry: ProviderRegistry2 = _emptyproviderregistry,
    /,
    **providerfactories: ProviderFactory2,
) -> ProviderRegistry2:
    """Register provider factories."""
    return {**providerregistry, **providerfactories}


def constproviderfactory(provider: Provider2) -> ProviderFactory2:
    """Create a provider factory that returns the given provider."""

    def _providerfactory(store: Store, fetchmode: FetchMode) -> Provider2:
        return provider

    return _providerfactory


def _createprovider(
    providername: ProviderName,
    providerfactory: ProviderFactory2,
    providerstore: ProviderStore,
    fetchmode: FetchMode,
) -> Provider2:
    """Create a provider."""
    store = providerstore(providername)
    return providerfactory(store, fetchmode)


def _createproviders(
    providerregistry: ProviderRegistry2,
    providerstore: ProviderStore,
    fetchmode: FetchMode,
    providername: Optional[ProviderName],
) -> Iterator[Provider2]:
    """Create providers."""
    if providername is not None:
        providerfactory = providerregistry[providername]
        yield _createprovider(providername, providerfactory, providerstore, fetchmode)
    else:
        for providername, providerfactory in providerregistry.items():
            yield _createprovider(
                providername, providerfactory, providerstore, fetchmode
            )


def _splitprovidername(location: Location) -> tuple[Optional[ProviderName], Location]:
    """Split off the provider name from the URL scheme, if any."""
    if isinstance(location, URL):
        providername, _, scheme = location.scheme.rpartition("+")

        if providername:
            return providername, location.with_scheme(scheme)

    return None, location


def repositoryprovider(
    providerregistry: ProviderRegistry2, providerstore: ProviderStore
) -> RepositoryProvider:
    """Return a repository provider."""

    def _provide(
        location: str,
        revision: Optional[Revision] = None,
        fetchmode: FetchMode = FetchMode.ALWAYS,
        directory: Optional[PurePath] = None,
    ) -> Repository:
        location_ = parselocation(location)
        providername, location_ = _splitprovidername(location_)
        providers = _createproviders(
            providerregistry, providerstore, fetchmode, providername
        )

        repository = provide(providers, location_, revision)

        if directory is not None:
            name = directory.name
            path = Path(
                filesystem=PathFilesystem(repository.path.joinpath(*directory.parts))
            )
            return Repository(name, path, repository.revision)

        return repository

    return _provide
