"""Fixtures for cutty.packages.domain.providers."""
from collections.abc import Callable
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.packages.domain.locations import Location
from cutty.packages.domain.package import Package
from cutty.packages.domain.providers import Provider
from cutty.packages.domain.repository import PackageRepository
from cutty.packages.domain.revisions import Revision


pytest_plugins = ["tests.fixtures.packages.domain.stores"]


ProviderFunction = Callable[[Location], Optional[PackageRepository]]


def provider(name: str) -> Callable[[ProviderFunction], Provider]:
    """Decorator to create a provider from a function."""

    def _decorator(function: ProviderFunction) -> Provider:
        class _Provider(Provider):
            def __init__(self) -> None:
                super().__init__(name)

            def provide(self, location: Location) -> Optional[PackageRepository]:
                """Retrieve the package repository at the given location."""
                return function(location)

        return _Provider()

    return _decorator


nullprovider = Provider("null")
"""Provider that matches no location."""


@dataclass
class SinglePackageRepository(PackageRepository):
    """A package repository with a single package."""

    package: Package

    @contextmanager
    def get(self, revision: Optional[Revision] = None) -> Iterator[Package]:
        """Retrieve the package with the given revision."""
        yield self.package


def constprovider(name: str, package: Package) -> Provider:
    """Provider that returns the same package always."""

    @provider(name)
    def _(location: Location) -> Optional[PackageRepository]:
        return SinglePackageRepository(package)

    return _


def dictprovider(
    mapping: Optional[dict[str, Any]] = None, name: str = "dict"
) -> Provider:
    """Provider that matches every URL with a package."""

    @provider(name)
    def _(location: Location) -> Optional[PackageRepository]:
        class _PackageRepository(PackageRepository):
            @contextmanager
            def get(self, revision: Optional[Revision] = None) -> Iterator[Package]:
                filesystem = DictFilesystem(mapping or {})
                path = Path(filesystem=filesystem)
                yield Package(location.name, path, revision)

        return _PackageRepository()

    return _
