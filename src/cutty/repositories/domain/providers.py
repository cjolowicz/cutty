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

from cutty.errors import CuttyError
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


Provider = Callable[[Location, Optional[Revision]], Optional[Repository]]


@dataclass
class UnknownLocationError(CuttyError):
    """The repository location could not be processed by any provider."""

    location: Location


def provide(
    providers: Iterable[Provider], location: Location, revision: Optional[Revision]
) -> Repository:
    """Provide the repository located at the given URL."""
    for provider in providers:
        if repository := provider(location, revision):
            return repository

    raise UnknownLocationError(location)


ProviderFactory = Callable[[Store, FetchMode], Provider]
GetRevision = Callable[[pathlib.Path, Optional[Revision]], Optional[Revision]]


def localprovider(
    *, match: PathMatcher, mount: Mounter, getrevision: Optional[GetRevision] = None
) -> Provider:
    """Create a view onto the local filesystem."""

    def _provider(
        location: Location, revision: Optional[Revision]
    ) -> Optional[Repository]:
        try:
            path_ = location if isinstance(location, pathlib.Path) else aspath(location)
        except ValueError:
            return None

        if not match(path_):
            return None

        filesystem = mount(path_, revision)
        path = Path(filesystem=filesystem)

        if getrevision is not None:
            revision = getrevision(path_, revision)

        return Repository(location.name, path, revision)

    return _provider


def _defaultmount(path: pathlib.Path, revision: Optional[Revision]) -> Filesystem:
    return DiskFilesystem(path)


def remoteproviderfactory(
    *,
    match: Optional[Matcher] = None,
    fetch: Iterable[Fetcher],
    mount: Optional[Mounter] = None,
    getrevision: Optional[GetRevision] = None,
) -> ProviderFactory:
    """Remote providers fetch the repository into local storage first."""
    fetch = tuple(fetch)
    _mount = mount if mount is not None else _defaultmount

    def _remoteproviderfactory(store: Store, fetchmode: FetchMode) -> Provider:
        def _remoteprovider(
            location: Location, revision: Optional[Revision]
        ) -> Optional[Repository]:
            url = location if isinstance(location, URL) else asurl(location)
            if match is None or match(url):
                for fetcher in fetch:
                    path = fetcher(url, store, revision, fetchmode)
                    if path is not None:
                        filesystem = _mount(path, revision)
                        path_ = Path(filesystem=filesystem)

                        if getrevision is not None:
                            revision = getrevision(path, revision)

                        return Repository(location.name, path_, revision)

            return None

        return _remoteprovider

    return _remoteproviderfactory


ProviderName = str
ProviderStore = Callable[[ProviderName], Store]
ProviderRegistry = Mapping[ProviderName, ProviderFactory]


_emptyproviderregistry: ProviderRegistry = MappingProxyType({})


def constproviderfactory(provider: Provider) -> ProviderFactory:
    """Create a provider factory that returns the given provider."""

    def _providerfactory(store: Store, fetchmode: FetchMode) -> Provider:
        return provider

    return _providerfactory


def _createprovider(
    providername: ProviderName,
    providerfactory: ProviderFactory,
    providerstore: ProviderStore,
    fetchmode: FetchMode,
) -> Provider:
    """Create a provider."""
    store = providerstore(providername)
    return providerfactory(store, fetchmode)


def _createproviders(
    providerregistry: ProviderRegistry,
    providerstore: ProviderStore,
    fetchmode: FetchMode,
    providername: Optional[ProviderName],
) -> Iterator[Provider]:
    """Create providers."""
    if providername is not None:
        providerfactory = providerregistry[providername]
        yield _createprovider(providername, providerfactory, providerstore, fetchmode)
    else:
        for providername, providerfactory in providerregistry.items():
            yield _createprovider(
                providername, providerfactory, providerstore, fetchmode
            )


def _splitprovidername(
    location: Location, providerregistry: ProviderRegistry
) -> tuple[Optional[ProviderName], Location]:
    """Split off the provider name from the URL scheme, if any."""
    if isinstance(location, URL):
        providername, _, scheme = location.scheme.rpartition("+")

        if providername and providername in providerregistry:
            return providername, location.with_scheme(scheme)

    return None, location


def repositoryprovider(
    providerregistry: ProviderRegistry, providerstore: ProviderStore
) -> RepositoryProvider:
    """Return a repository provider."""

    def _provide(
        location: str,
        revision: Optional[Revision] = None,
        fetchmode: FetchMode = FetchMode.ALWAYS,
        directory: Optional[PurePath] = None,
    ) -> Repository:
        location_ = parselocation(location)
        providername, location_ = _splitprovidername(location_, providerregistry)
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
