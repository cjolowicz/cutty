"""Package providers."""
import abc
import pathlib
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Optional

from yarl import URL

from cutty.compat.contextlib import contextmanager
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.packages.domain.fetchers import Fetcher
from cutty.packages.domain.locations import asurl
from cutty.packages.domain.locations import Location
from cutty.packages.domain.locations import pathfromlocation
from cutty.packages.domain.matchers import Matcher
from cutty.packages.domain.matchers import PathMatcher
from cutty.packages.domain.mounters import Mounter
from cutty.packages.domain.repository import DefaultPackageRepository
from cutty.packages.domain.repository import GetMessage
from cutty.packages.domain.repository import GetRevision
from cutty.packages.domain.repository import PackageRepository
from cutty.packages.domain.repository import PackageRepositoryProvider
from cutty.packages.domain.revisions import Revision
from cutty.packages.domain.stores import Store


class Provider:
    """Provider for a specific type of package."""

    def __init__(self, name: str = "") -> None:
        """Initialize."""
        self.name = name

    def provide(self, location: Location) -> Optional[PackageRepository]:
        """Retrieve the package repository at the given location."""


class LocalProvider(Provider):
    """Provide a package from the local filesystem."""

    def __init__(
        self,
        name: str = "local",
        /,
        *,
        match: PathMatcher,
        mount: Optional[Mounter] = None,
        getcommit: Optional[GetRevision] = None,
        getrevision: Optional[GetRevision] = None,
        getparentrevision: Optional[GetRevision] = None,
        getmessage: Optional[GetMessage] = None,
        provider: Optional[PackageRepositoryProvider] = None,
    ) -> None:
        """Initialize."""
        super().__init__(name)

        self.match = match
        self.mount = mount
        self.getcommit = getcommit
        self.getrevision = getrevision
        self.getparentrevision = getparentrevision
        self.getmessage = getmessage
        self.provider = provider

    def provide(self, location: Location) -> Optional[PackageRepository]:
        """Retrieve the package repository at the given location."""
        if path := pathfromlocation(location):
            if path.exists() and self.match(path):
                if self.provider is not None:
                    return self.provider.provide(location.name, path)

                assert self.mount is not None  # noqa: S101

                return DefaultPackageRepository(
                    location.name,
                    path,
                    mount=self.mount,
                    getcommit=self.getcommit,
                    getrevision=self.getrevision,
                    getparentrevision=self.getparentrevision,
                    getmessage=self.getmessage,
                )

        return None


@contextmanager
def _defaultmount(
    path: pathlib.Path, revision: Optional[Revision]
) -> Iterator[Filesystem]:
    yield DiskFilesystem(path)


class RemoteProvider(Provider):
    """Remote providers fetch the package into local storage first."""

    def __init__(
        self,
        name: str = "remote",
        /,
        *,
        match: Optional[Matcher] = None,
        fetch: Iterable[Fetcher],
        mount: Optional[Mounter] = None,
        getcommit: Optional[GetRevision] = None,
        getrevision: Optional[GetRevision] = None,
        getparentrevision: Optional[GetRevision] = None,
        getmessage: Optional[GetMessage] = None,
        provider: Optional[PackageRepositoryProvider] = None,
        store: Store,
    ) -> None:
        """Initialize."""
        super().__init__(name)

        if mount is None:
            mount = _defaultmount

        if match is None:
            match = lambda _: True  # noqa: E731

        self.match = match
        self.fetch = tuple(fetch)
        self.store = store
        self.mount = mount
        self.getcommit = getcommit
        self.getrevision = getrevision
        self.getparentrevision = getparentrevision
        self.getmessage = getmessage
        self.provider = provider

    def provide(self, location: Location) -> Optional[PackageRepository]:
        """Retrieve the package repository at the given location."""
        if isinstance(location, URL):
            url = location
        elif location.exists():
            url = asurl(location)
        else:
            return None

        if self.match(url):
            for fetcher in self.fetch:
                if fetcher.match(url):
                    path = fetcher.fetch(url, self.store)
                    if self.provider is not None:
                        return self.provider.provide(location.name, path)

                    return DefaultPackageRepository(
                        location.name,
                        path,
                        mount=self.mount,
                        getcommit=self.getcommit,
                        getrevision=self.getrevision,
                        getparentrevision=self.getparentrevision,
                        getmessage=self.getmessage,
                    )

        return None


class ProviderFactory(abc.ABC):
    """Provider factory."""

    def __init__(self, name: str = "") -> None:
        """Initialize."""
        self.name = name

    @abc.abstractmethod
    def __call__(self, store: Store) -> Provider:
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
        getcommit: Optional[GetRevision] = None,
        getrevision: Optional[GetRevision] = None,
        getparentrevision: Optional[GetRevision] = None,
        getmessage: Optional[GetMessage] = None,
    ) -> None:
        """Initialize."""
        super().__init__(name)
        self.match = match
        self.fetch = tuple(fetch)
        self.mount = mount
        self.getcommit = getcommit
        self.getrevision = getrevision
        self.getparentrevision = getparentrevision
        self.getmessage = getmessage

    def __call__(self, store: Store) -> Provider:
        """Create a provider."""
        return RemoteProvider(
            self.name,
            match=self.match,
            fetch=self.fetch,
            mount=self.mount,
            getcommit=self.getcommit,
            getrevision=self.getrevision,
            getparentrevision=self.getparentrevision,
            getmessage=self.getmessage,
            store=store,
        )


class ConstProviderFactory(ProviderFactory):
    """Provider factory returning a given provider."""

    def __init__(self, provider: Provider) -> None:
        """Initialize."""
        super().__init__(provider.name)
        self.provider = provider

    def __call__(self, store: Store) -> Provider:
        """Return the provider."""
        return self.provider
