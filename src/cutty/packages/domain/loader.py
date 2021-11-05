"""Loaders for package repositories."""
import abc
import pathlib
from contextlib import AbstractContextManager
from typing import Optional

from cutty.filesystems.domain.filesystem import Filesystem
from cutty.packages.domain.mounters import Mounter
from cutty.packages.domain.repository import DefaultPackageRepository
from cutty.packages.domain.repository import PackageRepository
from cutty.packages.domain.revisions import Revision


class PackageRepositoryLoader(abc.ABC):
    """Loader for package repositories."""

    @abc.abstractmethod
    def load(self, name: str, path: pathlib.Path) -> PackageRepository:
        """Load a package repository from disk."""


class DefaultPackageRepositoryLoader(PackageRepositoryLoader):
    """Default implementation of a repository loader."""

    def load(self, name: str, path: pathlib.Path) -> PackageRepository:
        """Load a package repository from disk."""
        return DefaultPackageRepository(name, path)


class MountedPackageRepositoryLoader(PackageRepositoryLoader):
    """Repository loader with a custom mounter."""

    def __init__(self, mount: Mounter) -> None:
        """Initialize."""
        self.mount = mount

    def load(self, name: str, path: pathlib.Path) -> PackageRepository:
        """Load a package repository from disk."""
        mount = self.mount

        class _Repository(DefaultPackageRepository):
            def mount(
                self, revision: Optional[Revision]
            ) -> AbstractContextManager[Filesystem]:
                return mount(self.path, revision)

        return _Repository(name, path)
