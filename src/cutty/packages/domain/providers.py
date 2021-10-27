"""Package providers."""
import abc
import pathlib
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Optional

from yarl import URL

from cutty.compat.contextlib import contextmanager
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.path import Path
from cutty.packages.domain.fetchers import Fetcher
from cutty.packages.domain.fetchers import FetchMode
from cutty.packages.domain.locations import aspath
from cutty.packages.domain.locations import asurl
from cutty.packages.domain.locations import Location
from cutty.packages.domain.matchers import Matcher
from cutty.packages.domain.matchers import PathMatcher
from cutty.packages.domain.mounters import Mounter
from cutty.packages.domain.package import Package
from cutty.packages.domain.package import PackageRepository
from cutty.packages.domain.revisions import Revision
from cutty.packages.domain.stores import Store


class Provider:
    """Provider for a specific type of package."""

    def __init__(self, name: str = "") -> None:
        """Initialize."""
        self.name = name

    def provide(self, location: Location) -> Optional[PackageRepository]:
        """Retrieve the package repository at the given location."""


GetRevision = Callable[[pathlib.Path, Optional[Revision]], Optional[Revision]]


class DefaultPackageRepository(PackageRepository):
    """Default implementation of a package repository."""

    def __init__(
        self,
        name: str,
        path: pathlib.Path,
        *,
        mount: Mounter,
        getrevision: Optional[GetRevision],
    ) -> None:
        """Initialize."""
        self.name = name
        self.path = path
        self.mount = mount
        self.getrevision = getrevision

    @contextmanager
    def get(self, revision: Optional[Revision] = None) -> Iterator[Package]:
        """Retrieve the package with the given revision."""
        if self.getrevision is not None:
            resolved_revision = self.getrevision(self.path, revision)
        else:
            resolved_revision = revision

        with self.mount(self.path, revision) as filesystem:
            yield Package(self.name, Path(filesystem=filesystem), resolved_revision)


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
        self, location: Location, path: pathlib.Path
    ) -> PackageRepository:
        return DefaultPackageRepository(
            location.name, path, mount=self.mount, getrevision=self.getrevision
        )


class LocalProvider(BaseProvider):
    """Provide a package from the local filesystem."""

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

    def provide(self, location: Location) -> Optional[PackageRepository]:
        """Retrieve the package repository at the given location."""
        try:
            path = location if isinstance(location, pathlib.Path) else aspath(location)
        except ValueError:
            return None

        if path.exists() and self.match(path):
            return self._loadrepository(location, path)

        return None


@contextmanager
def _defaultmount(
    path: pathlib.Path, revision: Optional[Revision]
) -> Iterator[Filesystem]:
    yield DiskFilesystem(path)


class RemoteProvider(BaseProvider):
    """Remote providers fetch the package into local storage first."""

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
        if mount is None:
            mount = _defaultmount

        super().__init__(name, mount=mount, getrevision=getrevision)
        self.match = match
        self.fetch = tuple(fetch)
        self.store = store
        self.fetchmode = fetchmode

    def provide(self, location: Location) -> Optional[PackageRepository]:
        """Retrieve the package repository at the given location."""
        if isinstance(location, URL):
            url = location
        elif location.exists():
            url = asurl(location)
        else:
            return None

        if self.match is None or self.match(url):
            for fetcher in self.fetch:
                if fetcher.match(url):
                    path = fetcher.fetch(url, self.store, self.fetchmode)
                    return self._loadrepository(location, path)

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
        self.fetch = tuple(fetch)
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
