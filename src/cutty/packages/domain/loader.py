"""Loaders for package repositories."""
import abc
import pathlib

from cutty.packages.domain.mounters import Mounter
from cutty.packages.domain.repository import DefaultPackageRepository
from cutty.packages.domain.repository import PackageRepository


class PackageRepositoryLoader(abc.ABC):
    """Loader for package repositories."""

    @abc.abstractmethod
    def load(self, name: str, path: pathlib.Path) -> PackageRepository:
        """Load a package repository from disk."""


class MountedPackageRepositoryLoader(PackageRepositoryLoader):
    """Loader for repositories of mounted packages."""

    def __init__(self, mount: Mounter) -> None:
        """Initialize."""
        self.mount = mount

    def load(self, name: str, path: pathlib.Path) -> PackageRepository:
        """Load a package repository from disk."""
        return DefaultPackageRepository(name, path, mount=self.mount)
