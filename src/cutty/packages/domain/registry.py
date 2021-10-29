"""The provider registry is the main entry point of cutty.packages."""
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

from yarl import URL

from cutty.errors import CuttyError
from cutty.packages.domain.locations import Location
from cutty.packages.domain.locations import parselocation
from cutty.packages.domain.providers import Provider
from cutty.packages.domain.providers import ProviderFactory
from cutty.packages.domain.repository import PackageRepository
from cutty.packages.domain.stores import Store


@dataclass
class UnknownLocationError(CuttyError):
    """The package location could not be processed by any provider."""

    location: Location


ProviderName = str
ProviderStore = Callable[[ProviderName], Store]


class ProviderRegistry:
    """The provider registry retrieves packages using registered providers."""

    def __init__(
        self, store: ProviderStore, factories: Iterable[ProviderFactory]
    ) -> None:
        """Initialize."""
        self.store = store
        self.registry = {factory.name: factory for factory in factories}

    def getrepository(self, rawlocation: str) -> PackageRepository:
        """Return the package repository located at the given location."""
        name, location = self._parselocation(rawlocation)

        for provider in self._createproviders(name):
            if repository := provider.provide(location):
                return repository

        raise UnknownLocationError(location)

    def _parselocation(self, rawlocation: str) -> tuple[Optional[str], Location]:
        """Parse the location and provider name, if any."""
        location = parselocation(rawlocation)

        if isinstance(location, URL):
            name, _, scheme = location.scheme.rpartition("+")

            if name and name in self.registry:
                return name, _withscheme(location, scheme)

        return None, location

    def _createproviders(self, name: Optional[str]) -> Iterator[Provider]:
        """Create providers."""
        if name is not None:
            factory = self.registry[name]
            yield self._createprovider(factory)
        else:
            for factory in self.registry.values():
                yield self._createprovider(factory)

    def _createprovider(self, factory: ProviderFactory) -> Provider:
        """Create a provider."""
        store = self.store(factory.name)
        return factory(store)


def _withscheme(url: URL, scheme: str) -> URL:
    if url.raw_host is not None:
        return url.with_scheme(scheme)

    # yarl does not allow scheme replacement in URLs without host
    # https://github.com/aio-libs/yarl/issues/280
    url = URL.build(
        scheme=scheme,
        authority=url.raw_authority,
        path=url.raw_path,
        query_string=url.raw_query_string,
        fragment=url.raw_fragment,
        encoded=True,
    )
    return url
