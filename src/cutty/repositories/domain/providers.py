"""Repository providers."""
import abc
import pathlib
from collections.abc import Callable
from collections.abc import Iterable
from typing import Optional

from yarl import URL

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
from cutty.repositories.domain.repository import Repository
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import Store


class Provider:
    """Provider for a specific type of repository."""

    def __init__(self, name: str = "") -> None:
        """Initialize."""
        self.name = name

    def __call__(
        self, location: Location, revision: Optional[Revision] = None
    ) -> Optional[Repository]:
        """Return the repository at the given location."""


GetRevision = Callable[[pathlib.Path, Optional[Revision]], Optional[Revision]]


class BaseProvider(Provider):
    """Base class for local and remote providers."""

    def __init__(
        self,
        name: str = "",
        /,
        *,
        mount: Mounter,
        getrevision: Optional[GetRevision] = None,
    ) -> None:
        """Initialize."""
        super().__init__(name)

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
        name: str = "local",
        /,
        *,
        match: PathMatcher,
        mount: Mounter,
        getrevision: Optional[GetRevision] = None,
    ) -> None:
        """Initialize."""
        super().__init__(name, mount=mount, getrevision=getrevision)
        self.match = match

    def __call__(
        self, location: Location, revision: Optional[Revision] = None
    ) -> Optional[Repository]:
        """Return the repository at the given location."""
        try:
            path = location if isinstance(location, pathlib.Path) else aspath(location)
        except ValueError:
            return None

        if path.exists() and self.match(path):
            return self._loadrepository(location, revision, path)

        return None


def _defaultmount(path: pathlib.Path, revision: Optional[Revision]) -> Filesystem:
    return DiskFilesystem(path)


class RemoteProvider(BaseProvider):
    """Remote providers fetch the repository into local storage first."""

    def __init__(
        self,
        name: str = "remote",
        /,
        *,
        match: Optional[Matcher] = None,
        fetch: Iterable[Fetcher],
        mount: Optional[Mounter] = None,
        getrevision: Optional[GetRevision] = None,
        store: Store,
        fetchmode: FetchMode = FetchMode.ALWAYS,
    ) -> None:
        """Initialize."""
        super().__init__(
            name,
            mount=mount if mount is not None else _defaultmount,
            getrevision=getrevision,
        )
        self.match = match
        self.fetch = tuple(fetch)
        self.store = store
        self.fetchmode = fetchmode

    def __call__(
        self, location: Location, revision: Optional[Revision] = None
    ) -> Optional[Repository]:
        """Return the repository at the given location."""
        if isinstance(location, URL):
            url = location
        elif location.exists():
            url = asurl(location)
        else:
            return None

        if self.match is None or self.match(url):
            for fetcher in self.fetch:
                if path := fetcher(url, self.store, revision, self.fetchmode):
                    return self._loadrepository(location, revision, path)

        return None


ProviderName = str
ProviderStore = Callable[[ProviderName], Store]


class ProviderFactory(abc.ABC):
    """Provider factory."""

    def __init__(self, name: str = "") -> None:
        """Initialize."""
        self.name = name

    @abc.abstractmethod
    def __call__(
        self, store: Store, fetchmode: FetchMode = FetchMode.ALWAYS
    ) -> Provider:
        """Create a provider."""


class RemoteProviderFactory(ProviderFactory):
    """Factory for remote providers."""

    def __init__(
        self,
        name: str = "remote",
        /,
        *,
        match: Optional[Matcher] = None,
        fetch: Iterable[Fetcher],
        mount: Optional[Mounter] = None,
        getrevision: Optional[GetRevision] = None,
    ) -> None:
        """Initialize."""
        super().__init__(name)
        self.match = match
        self.fetch = fetch
        self.mount = mount
        self.getrevision = getrevision

    def __call__(
        self, store: Store, fetchmode: FetchMode = FetchMode.ALWAYS
    ) -> Provider:
        """Create a provider."""
        return RemoteProvider(
            self.name,
            match=self.match,
            fetch=self.fetch,
            mount=self.mount,
            getrevision=self.getrevision,
            store=store,
            fetchmode=fetchmode,
        )


class ConstProviderFactory(ProviderFactory):
    """Provider factory returning a given provider."""

    def __init__(self, provider: Provider) -> None:
        """Initialize."""
        super().__init__(provider.name)
        self.provider = provider

    def __call__(
        self, store: Store, fetchmode: FetchMode = FetchMode.ALWAYS
    ) -> Provider:
        """Return the provider."""
        return self.provider
