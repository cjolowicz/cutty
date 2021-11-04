"""Package repositories."""
import abc
import pathlib
from collections.abc import Iterator
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.errors import CuttyError
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.path import Path
from cutty.packages.domain.mounters import Mounter
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


@contextmanager
def _defaultmount(
    path: pathlib.Path, revision: Optional[Revision]
) -> Iterator[Filesystem]:
    yield DiskFilesystem(path)


class DefaultPackageRepository(PackageRepository):
    """Default implementation of a package repository."""

    def __init__(
        self, name: str, path: pathlib.Path, *, mount: Mounter = _defaultmount
    ) -> None:
        """Initialize."""
        self.name = name
        self.path = path
        self._mount = mount

    @contextmanager
    def get(self, revision: Optional[Revision] = None) -> Iterator[Package]:
        """Retrieve the package with the given revision."""
        commit = self.getcommit(revision)
        resolved_revision = self.getrevision(revision)
        message = self.getmessage(revision)

        with self.mount(revision) as filesystem:
            tree = Path(filesystem=filesystem)

            yield Package(self.name, tree, resolved_revision, commit, message)

    def mount(self, revision: Optional[Revision]) -> AbstractContextManager[Filesystem]:
        """Mount the package filesystem."""
        return self._mount(self.path, revision)

    def getcommit(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the commit identifier."""
        return None

    def getrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the resolved revision."""
        return revision

    def getparentrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the parent revision, if any."""
        raise ParentRevisionNotImplementedError(self.name)

    def getmessage(self, revision: Optional[Revision]) -> Optional[str]:
        """Return the commit message."""
        return None
