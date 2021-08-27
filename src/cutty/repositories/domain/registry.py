"""The provider registry is the main entry point of cutty.repositories."""
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional

from yarl import URL

from cutty.errors import CuttyError
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.pathfs import PathFilesystem
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
    providers: Iterable[Provider], location: Location, revision: Optional[Revision]
) -> Repository:
    """Provide the repository located at the given URL."""
    for provider in providers:
        if repository := provider(location, revision):
            return repository

    raise UnknownLocationError(location)


class ProviderRegistry:
    """The provider registry retrieves repositories using registered providers."""

    def __init__(
        self, registry: Mapping[ProviderName, ProviderFactory], store: ProviderStore
    ) -> None:
        """Initialize."""
        self.registry = registry
        self.store = store

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

        if directory is not None:
            name = directory.name
            path = Path(
                filesystem=PathFilesystem(repository.path.joinpath(*directory.parts))
            )
            return Repository(name, path, repository.revision)

        return repository

    def _extractprovidername(
        self, location: Location
    ) -> tuple[Optional[ProviderName], Location]:
        """Split off the provider name from the URL scheme, if any."""
        if isinstance(location, URL):
            providername, _, scheme = location.scheme.rpartition("+")

            if providername and providername in self.registry:
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
            yield self._createprovider(providername, providerfactory, fetchmode)
        else:
            for providername, providerfactory in self.registry.items():
                yield self._createprovider(providername, providerfactory, fetchmode)

    def _createprovider(
        self,
        providername: ProviderName,
        providerfactory: ProviderFactory,
        fetchmode: FetchMode,
    ) -> Provider:
        """Create a provider."""
        store = self.store(providername)
        return providerfactory(store, fetchmode)
