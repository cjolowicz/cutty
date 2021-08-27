"""Repository providers."""
import pathlib
from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional

from yarl import URL

from cutty.errors import CuttyError
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import aspath
from cutty.repositories.domain.locations import asurl
from cutty.repositories.domain.locations import Location
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


class Provider:
    """Provider for a specific type of repository."""

    def __call__(
        self, location: Location, revision: Optional[Revision]
    ) -> Optional[Repository]:
        """Return the repository at the given location."""


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


GetRevision = Callable[[pathlib.Path, Optional[Revision]], Optional[Revision]]


class BaseProvider(Provider):
    """Base class for local and remote providers."""

    def __init__(
        self,
        *,
        mount: Mounter,
        getrevision: Optional[GetRevision] = None,
    ) -> None:
        """Initialize."""
        self.mount = mount
        self.getrevision = getrevision

    def _loadrepository(
        self, location: Location, revision: Optional[Revision], path: pathlib.Path
    ) -> Repository:
        filesystem = self.mount(path, revision)

        if self.getrevision is not None:
            revision = self.getrevision(path, revision)

        return Repository(location.name, Path(filesystem=filesystem), revision)


class LocalProvider(BaseProvider):
    """Provide a repository from the local filesystem."""

    def __init__(
        self,
        *,
        match: PathMatcher,
        mount: Mounter,
        getrevision: Optional[GetRevision] = None,
    ) -> None:
        """Initialize."""
        super().__init__(mount=mount, getrevision=getrevision)
        self.match = match

    def __call__(
        self, location: Location, revision: Optional[Revision]
    ) -> Optional[Repository]:
        """Return the repository at the given location."""
        try:
            path = location if isinstance(location, pathlib.Path) else aspath(location)
        except ValueError:
            return None

        if self.match(path):
            return self._loadrepository(location, revision, path)

        return None


def _defaultmount(path: pathlib.Path, revision: Optional[Revision]) -> Filesystem:
    return DiskFilesystem(path)


class RemoteProvider(BaseProvider):
    """Remote providers fetch the repository into local storage first."""

    def __init__(
        self,
        *,
        match: Optional[Matcher] = None,
        fetch: Iterable[Fetcher],
        mount: Optional[Mounter] = None,
        getrevision: Optional[GetRevision] = None,
        store: Store,
        fetchmode: FetchMode,
    ) -> None:
        """Initialize."""
        super().__init__(
            mount=mount if mount is not None else _defaultmount, getrevision=getrevision
        )
        self.match = match
        self.fetch = tuple(fetch)
        self.store = store
        self.fetchmode = fetchmode

    def __call__(
        self, location: Location, revision: Optional[Revision]
    ) -> Optional[Repository]:
        """Return the repository at the given location."""
        url = location if isinstance(location, URL) else asurl(location)

        if self.match is None or self.match(url):
            for fetcher in self.fetch:
                if path := fetcher(url, self.store, revision, self.fetchmode):
                    return self._loadrepository(location, revision, path)

        return None


ProviderName = str
ProviderStore = Callable[[ProviderName], Store]
ProviderFactory = Callable[[Store, FetchMode], Provider]


def remoteproviderfactory(
    *,
    match: Optional[Matcher] = None,
    fetch: Iterable[Fetcher],
    mount: Optional[Mounter] = None,
    getrevision: Optional[GetRevision] = None,
) -> ProviderFactory:
    """Remote providers fetch the repository into local storage first."""

    def _remoteproviderfactory(store: Store, fetchmode: FetchMode) -> Provider:
        return RemoteProvider(
            match=match,
            fetch=fetch,
            mount=mount,
            getrevision=getrevision,
            store=store,
            fetchmode=fetchmode,
        )

    return _remoteproviderfactory


def constproviderfactory(provider: Provider) -> ProviderFactory:
    """Create a provider factory that returns the given provider."""

    def _providerfactory(store: Store, fetchmode: FetchMode) -> Provider:
        return provider

    return _providerfactory
