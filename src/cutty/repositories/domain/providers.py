"""Repository providers."""
import pathlib
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional
from typing import Protocol

from yarl import URL

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.matchers import Matcher
from cutty.repositories.domain.matchers import PathMatcher
from cutty.repositories.domain.mounters import Mounter
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import Store
from cutty.repositories.domain.urls import aspath
from cutty.repositories.domain.urls import parseurl


class RepositoryProvider(Protocol):
    """The repository provider turns a repository URL into a filesystem path."""

    def __call__(
        self,
        location: str,
        revision: Optional[Revision] = None,
        fetchmode: FetchMode = FetchMode.ALWAYS,
    ) -> Path:
        """Return a path to the repository located at the given URL."""


Provider = Callable[[URL, Optional[Revision]], Optional[Filesystem]]


def provide(
    providers: Iterable[Provider], url: URL, revision: Optional[Revision]
) -> Path:
    """Provide a filesystem path for the repository located at the given URL."""
    for provider in providers:
        filesystem = provider(url, revision)
        if filesystem is not None:
            return Path(filesystem=filesystem)

    raise RuntimeError(f"unknown location {url}")


ProviderFactory = Callable[[Store, FetchMode], Provider]


def localprovider(*, match: PathMatcher, mount: Mounter) -> Provider:
    """Create a view onto the local filesystem."""

    def _localprovider(url: URL, revision: Optional[Revision]) -> Optional[Filesystem]:
        try:
            path = aspath(url)
        except ValueError:
            return None
        else:
            return mount(path, revision) if match(path) else None

    return _localprovider


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
            url: URL, revision: Optional[Revision]
        ) -> Optional[Filesystem]:
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


_emptyproviderregistry: ProviderRegistry = MappingProxyType({})


def registerproviderfactory(
    providerregistry: ProviderRegistry,
    providername: ProviderName,
    providerfactory: ProviderFactory,
) -> ProviderRegistry:
    """Register a provider factory."""
    return {**providerregistry, providername: providerfactory}


def registerproviderfactories(
    providerregistry: ProviderRegistry = _emptyproviderregistry,
    **providerfactories: ProviderFactory,
) -> ProviderRegistry:
    """Register provider factories."""
    return {**providerregistry, **providerfactories}


def constproviderfactory(provider: Provider) -> ProviderFactory:
    """Create a provider factory that returns the given provider."""

    def _providerfactory(store: Store, fetchmode: FetchMode) -> Provider:
        return provider

    return _providerfactory


def registerprovider(
    providerregistry: ProviderRegistry,
    providername: ProviderName,
    provider: Provider,
) -> ProviderRegistry:
    """Register a provider factory."""
    return {**providerregistry, providername: constproviderfactory(provider)}


def registerproviders(
    providerregistry: ProviderRegistry = _emptyproviderregistry,
    **providers: Provider,
) -> ProviderRegistry:
    """Register provider factories."""
    providerfactories = {
        providername: constproviderfactory(provider)
        for providername, provider in providers.items()
    }
    return {**providerregistry, **providerfactories}


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


def _splitprovidername(url: URL) -> tuple[Optional[ProviderName], URL]:
    """Split off the provider name from the URL scheme, if any."""
    providername, _, scheme = url.scheme.rpartition("+")

    if providername:
        return providername, url.with_scheme(scheme)

    return None, url


def repositoryprovider(
    providerregistry: ProviderRegistry, providerstore: ProviderStore
) -> RepositoryProvider:
    """Return a repository provider."""

    def _provide(
        location: str,
        revision: Optional[Revision] = None,
        fetchmode: FetchMode = FetchMode.ALWAYS,
    ) -> Path:
        url = parseurl(location)
        providername, url = _splitprovidername(url)
        providers = _createproviders(
            providerregistry, providerstore, fetchmode, providername
        )

        return provide(providers, url, revision)

    return _provide
