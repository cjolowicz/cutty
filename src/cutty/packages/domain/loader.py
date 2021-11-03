"""Loaders for package repositories."""
import abc
import pathlib

from cutty.packages.domain.repository import PackageRepository


class PackageRepositoryLoader(abc.ABC):
    """Loader for package repositories."""

    @abc.abstractmethod
    def load(self, name: str, path: pathlib.Path) -> PackageRepository:
        """Load a package repository from disk."""
