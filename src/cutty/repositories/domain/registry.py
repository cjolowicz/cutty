"""The provider registry is the main entry point of cutty.repositories."""
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

from yarl import URL

from cutty.errors import CuttyError
from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import Location
from cutty.repositories.domain.locations import parselocation
from cutty.repositories.domain.providers import Provider
from cutty.repositories.domain.providers import ProviderFactory
from cutty.repositories.domain.providers import ProviderName
from cutty.repositories.domain.providers import ProviderStore
from cutty.repositories.domain.repository import Repository
from cutty.repositories.domain.revisions import Revision


@dataclass
class UnknownLocationError(CuttyError):
    """The repository location could not be processed by any provider."""

    location: Location


def provide(
    providers: Iterable[Provider],
    location: Location,
    revision: Optional[Revision] = None,
) -> Repository:
    """Provide the repository located at the given URL."""
    for provider in providers:
        if repository := provider(location, revision):
            return repository

    raise UnknownLocationError(location)


class ProviderRegistry:
    """The provider registry retrieves repositories using registered providers."""

    def __init__(
        self,
        store: ProviderStore,
        factories: Iterable[ProviderFactory],
    ) -> None:
        """Initialize."""
        self.store = store
        self.registry = {
            providerfactory.name: providerfactory for providerfactory in factories
        }

    def __call__(
        self,
        rawlocation: str,
        revision: Optional[Revision] = None,
        fetchmode: FetchMode = FetchMode.ALWAYS,
        directory: Optional[PurePath] = None,
    ) -> Repository:
        """Return the repository located at the given URL."""
        location = parselocation(rawlocation)

        providername, location = self._extractprovidername(location)
        providers = self._createproviders(fetchmode, providername)
        repository = provide(providers, location, revision)

        return repository if directory is None else repository.descend(directory)

    def _extractprovidername(
        self, location: Location
    ) -> tuple[Optional[ProviderName], Location]:
        """Split off the provider name from the URL scheme, if any."""
        if isinstance(location, URL):
            providername, _, scheme = location.scheme.rpartition("+")

            if providername and providername in self.registry:
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
                    return providername, location
                return providername, location.with_scheme(scheme)

        return None, location

    def _createproviders(
        self,
        fetchmode: FetchMode,
        providername: Optional[ProviderName],
    ) -> Iterator[Provider]:
        """Create providers."""
        if providername is not None:
            providerfactory = self.registry[providername]
            yield self._createprovider(providerfactory, fetchmode)
        else:
            for providerfactory in self.registry.values():
                yield self._createprovider(providerfactory, fetchmode)

    def _createprovider(
        self,
        providerfactory: ProviderFactory,
        fetchmode: FetchMode,
    ) -> Provider:
        """Create a provider."""
        store = self.store(providerfactory.name)
        return providerfactory(store, fetchmode)
