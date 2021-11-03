"""Package repositories."""
import abc
import pathlib
from collections.abc import Callable
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.errors import CuttyError
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


class PackageRepositoryProvider(abc.ABC):
    """A provider of package repositories."""

    @abc.abstractmethod
    def provide(self, name: str, path: pathlib.Path) -> PackageRepository:
        """Load a package repository."""


GetRevision = Callable[[pathlib.Path, Optional[Revision]], Optional[Revision]]
GetMessage = Callable[[pathlib.Path, Optional[Revision]], Optional[str]]


class DefaultPackageRepository(PackageRepository):
    """Default implementation of a package repository."""

    def __init__(
        self,
        name: str,
        path: pathlib.Path,
        *,
        mount: Mounter,
        getcommit: Optional[GetRevision] = None,
        getrevision: Optional[GetRevision],
        getparentrevision: Optional[GetRevision] = None,
        getmessage: Optional[GetMessage] = None,
    ) -> None:
        """Initialize."""
        self.name = name
        self.path = path
        self.mount = mount
        self._getcommit = getcommit
        self._getrevision = getrevision
        self._getparentrevision = getparentrevision
        self._getmessage = getmessage

    @contextmanager
    def get(self, revision: Optional[Revision] = None) -> Iterator[Package]:
        """Retrieve the package with the given revision."""
        commit = self.getcommit(revision)
        resolved_revision = self.getrevision(revision)
        message = self.getmessage(revision)

        with self.mount(self.path, revision) as filesystem:
            tree = Path(filesystem=filesystem)

            yield Package(self.name, tree, resolved_revision, commit, message)

    def getcommit(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the commit identifier."""
        if self._getcommit is None:
            return None

        return self._getcommit(self.path, revision)

    def getrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the resolved revision."""
        if self._getrevision is None:
            return revision

        return self._getrevision(self.path, revision)

    def getparentrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the parent revision, if any."""
        if self._getparentrevision is None:
            raise ParentRevisionNotImplementedError(self.name)

        return self._getparentrevision(self.path, revision)

    def getmessage(self, revision: Optional[Revision]) -> Optional[str]:
        """Return the commit message."""
        if self._getmessage is None:
            return None

        return self._getmessage(self.path, revision)
