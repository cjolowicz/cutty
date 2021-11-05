"""Package providers."""
import abc
from collections.abc import Iterable
from typing import Optional

from yarl import URL

from cutty.packages.domain.fetchers import Fetcher
from cutty.packages.domain.loader import DefaultPackageRepositoryLoader
from cutty.packages.domain.loader import PackageRepositoryLoader
from cutty.packages.domain.locations import asurl
from cutty.packages.domain.locations import Location
from cutty.packages.domain.locations import pathfromlocation
from cutty.packages.domain.matchers import Matcher
from cutty.packages.domain.matchers import PathMatcher
from cutty.packages.domain.repository import PackageRepository
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
        match: Optional[PathMatcher] = None,
        loader: Optional[PackageRepositoryLoader] = None,
    ) -> None:
        """Initialize."""
        super().__init__(name)

        if match is None:
            match = lambda _: True  # noqa: E731

        if loader is None:
            loader = DefaultPackageRepositoryLoader()

        self.match = match
        self.loader = loader

    def provide(self, location: Location) -> Optional[PackageRepository]:
        """Retrieve the package repository at the given location."""
        if path := pathfromlocation(location):
            if path.exists() and self.match(path):
                return self.loader.load(location.name, path)

        return None


class RemoteProvider(Provider):
    """Remote providers fetch the package into local storage first."""

    def __init__(
        self,
        name: str = "remote",
        /,
        *,
        match: Optional[Matcher] = None,
        fetch: Iterable[Fetcher],
        loader: Optional[PackageRepositoryLoader] = None,
        store: Store,
    ) -> None:
        """Initialize."""
        super().__init__(name)

        if match is None:
            match = lambda _: True  # noqa: E731

        if loader is None:
            loader = DefaultPackageRepositoryLoader()

        self.match = match
        self.fetch = tuple(fetch)
        self.store = store
        self.loader = loader

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
                    return self.loader.load(location.name, path)

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
        loader: Optional[PackageRepositoryLoader] = None,
    ) -> None:
        """Initialize."""
        super().__init__(name)
        self.match = match
        self.fetch = tuple(fetch)
        self.loader = loader

    def __call__(self, store: Store) -> Provider:
        """Create a provider."""
        return RemoteProvider(
            self.name,
            match=self.match,
            fetch=self.fetch,
            loader=self.loader,
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
