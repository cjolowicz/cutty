"""Fixtures for cutty.repositories.domain.providers."""
from collections.abc import Callable
from typing import Any
from typing import Optional

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories.domain.locations import Location
from cutty.repositories.domain.providers import Provider
from cutty.repositories.domain.repository import Repository
from cutty.repositories.domain.revisions import Revision


ProviderFunction = Callable[[Location, Optional[Revision]], Optional[Repository]]


def provider(function: ProviderFunction) -> Provider:
    """Decorator to create a provider from a function."""

    class _Provider(Provider):
        def __call__(
            self, location: Location, revision: Optional[Revision]
        ) -> Optional[Repository]:
            return function(location, revision)

    return _Provider()


nullprovider = Provider()
"""Provider that matches no location."""


def constprovider(repository: Repository) -> Provider:
    """Provider that returns the same repository always."""

    @provider
    def _constprovider(
        location: Location, revision: Optional[Revision]
    ) -> Optional[Repository]:
        return repository

    return _constprovider


def dictprovider(mapping: Optional[dict[str, Any]] = None) -> Provider:
    """Provider that matches every URL with a repository."""

    @provider
    def _provider(
        location: Location, revision: Optional[Revision]
    ) -> Optional[Repository]:
        filesystem = DictFilesystem(mapping or {})
        if filesystem is not None:
            path = Path(filesystem=filesystem)
            return Repository(location.name, path, revision)
        return None

    return _provider