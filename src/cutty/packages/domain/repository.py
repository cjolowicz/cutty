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


GetRevision = Callable[[pathlib.Path, Optional[Revision]], Optional[Revision]]


class DefaultPackageRepository(PackageRepository):
    """Default implementation of a package repository."""

    def __init__(
        self,
        name: str,
        path: pathlib.Path,
        *,
        mount: Mounter,
        getrevision: Optional[GetRevision],
        getparentrevision: Optional[GetRevision] = None,
    ) -> None:
        """Initialize."""
        self.name = name
        self.path = path
        self.mount = mount
        self._getrevision = getrevision
        self._getparentrevision = getparentrevision

    @contextmanager
    def get(self, revision: Optional[Revision] = None) -> Iterator[Package]:
        """Retrieve the package with the given revision."""
        resolved_revision = self.getrevision(revision)

        with self.mount(self.path, revision) as filesystem:
            yield Package(self.name, Path(filesystem=filesystem), resolved_revision)

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
