"""Fixtures for cutty.repositories.domain.providers."""
from collections.abc import Callable
from typing import Any
from typing import Optional

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.packages.domain.locations import Location
from cutty.packages.domain.package import Package
from cutty.packages.domain.providers import Provider
from cutty.packages.domain.revisions import Revision


pytest_plugins = ["tests.fixtures.repositories.domain.stores"]


ProviderFunction = Callable[[Location, Optional[Revision]], Optional[Package]]


def provider(name: str) -> Callable[[ProviderFunction], Provider]:
    """Decorator to create a provider from a function."""

    def _decorator(function: ProviderFunction) -> Provider:
        class _Provider(Provider):
            def __init__(self) -> None:
                super().__init__(name)

            def __call__(
                self, location: Location, revision: Optional[Revision] = None
            ) -> Optional[Package]:
                return function(location, revision)

        return _Provider()

    return _decorator


nullprovider = Provider("null")
"""Provider that matches no location."""


def constprovider(name: str, repository: Package) -> Provider:
    """Provider that returns the same repository always."""

    @provider(name)
    def _(location: Location, revision: Optional[Revision]) -> Optional[Package]:
        return repository

    return _


def dictprovider(mapping: Optional[dict[str, Any]] = None) -> Provider:
    """Provider that matches every URL with a repository."""

    @provider("dict")
    def _(location: Location, revision: Optional[Revision]) -> Optional[Package]:
        filesystem = DictFilesystem(mapping or {})
        path = Path(filesystem=filesystem)
        return Package(location.name, path, revision)

    return _
