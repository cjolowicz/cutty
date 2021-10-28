"""The provider registry is the main entry point of cutty.packages."""
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

from yarl import URL

from cutty.errors import CuttyError
from cutty.packages.domain.fetchers import FetchMode
from cutty.packages.domain.locations import Location
from cutty.packages.domain.locations import parselocation
from cutty.packages.domain.package import PackageRepository
from cutty.packages.domain.providers import Provider
from cutty.packages.domain.providers import ProviderFactory
from cutty.packages.domain.providers import ProviderName
from cutty.packages.domain.providers import ProviderStore


@dataclass
class UnknownLocationError(CuttyError):
    """The package location could not be processed by any provider."""

    location: Location


class ProviderRegistry:
    """The provider registry retrieves packages using registered providers."""

    def __init__(
        self,
        store: ProviderStore,
        factories: Iterable[ProviderFactory],
    ) -> None:
        """Initialize."""
        self.store = store
        self.registry = {factory.name: factory for factory in factories}

    def getrepository(
        self, rawlocation: str, fetchmode: FetchMode = FetchMode.ALWAYS
    ) -> PackageRepository:
        """Return the package repository located at the given URL."""
        location = parselocation(rawlocation)
        name, location = self._extractname(location)
        providers = self._createproviders(fetchmode, name)

        for provider in providers:
            if repository := provider.provide(location):
                return repository

        raise UnknownLocationError(location)

    def _extractname(
        self, location: Location
    ) -> tuple[Optional[ProviderName], Location]:
        """Split off the provider name from the URL scheme, if any."""
        if isinstance(location, URL):
            name, _, scheme = location.scheme.rpartition("+")

            if name and name in self.registry:
                return name, _withscheme(location, scheme)

        return None, location

    def _createproviders(
        self, fetchmode: FetchMode, name: Optional[ProviderName]
    ) -> Iterator[Provider]:
        """Create providers."""
        if name is not None:
            factory = self.registry[name]
            yield self._createprovider(factory, fetchmode)
        else:
            for factory in self.registry.values():
                yield self._createprovider(factory, fetchmode)

    def _createprovider(
        self, factory: ProviderFactory, fetchmode: FetchMode
    ) -> Provider:
        """Create a provider."""
        store = self.store(factory.name)
        return factory(store, fetchmode)


def _withscheme(location: URL, scheme: str) -> URL:
    if location.raw_host is None:
        # yarl does not allow scheme replacement in URLs without host
        # https://github.com/aio-libs/yarl/issues/280
        location = URL.build(
            scheme=scheme,
            authority=location.raw_authority,
            path=location.raw_path,
            query_string=location.raw_query_string,
            fragment=location.raw_fragment,
            encoded=True,
        )
        return location
    return location.with_scheme(scheme)
