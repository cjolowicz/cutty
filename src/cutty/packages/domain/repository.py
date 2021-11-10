"""Package repositories."""
import abc
import pathlib
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.errors import CuttyError
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.path import Path
from cutty.packages.domain.package import Commit
from cutty.packages.domain.package import Package
from cutty.packages.domain.revisions import Revision


@dataclass
class ParentRevisionNotImplementedError(CuttyError):
    """The repository does not support `getparentrevision`."""

    name: str


class PackageRepository(abc.ABC):
    """A package repository."""

    @contextmanager
    @abc.abstractmethod
    def get(self, revision: Optional[Revision] = None) -> Iterator[Package]:
        """Retrieve the package with the given revision."""

    def getparentrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the parent revision, if any."""


class DefaultPackageRepository(PackageRepository):
    """Default implementation of a package repository."""

    def __init__(self, name: str, path: pathlib.Path) -> None:
        """Initialize."""
        self.name = name
        self.path = path

    @contextmanager
    def get(self, revision: Optional[Revision] = None) -> Iterator[Package]:
        """Retrieve the package with the given revision."""
        commit = self.lookup(revision)

        with self.mount(revision) as filesystem:
            tree = Path(filesystem=filesystem)

            yield Package(self.name, tree, commit)

    @contextmanager
    def mount(self, revision: Optional[Revision]) -> Iterator[Filesystem]:
        """Mount the package filesystem."""
        yield DiskFilesystem(self.path)

    def lookup(self, revision: Optional[Revision]) -> Optional[Commit]:
        """Look up the commit metadata for the given revision."""
        return None

    def getparentrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the parent revision, if any."""
        raise ParentRevisionNotImplementedError(self.name)
