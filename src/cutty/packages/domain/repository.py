"""Package repositories."""
import abc
import pathlib
from collections.abc import Callable
from collections.abc import Iterator
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.filesystems.domain.path import Path
from cutty.packages.domain.mounters import Mounter
from cutty.packages.domain.package import Package
from cutty.packages.domain.revisions import Revision


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
        self.getrevision = getrevision
        self._getparentrevision = getparentrevision

    @contextmanager
    def get(self, revision: Optional[Revision] = None) -> Iterator[Package]:
        """Retrieve the package with the given revision."""
        if self.getrevision is not None:
            resolved_revision = self.getrevision(self.path, revision)
        else:
            resolved_revision = revision

        with self.mount(self.path, revision) as filesystem:
            yield Package(self.name, Path(filesystem=filesystem), resolved_revision)

    def getparentrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the parent revision, if any."""
        if self._getparentrevision is None:
            raise NotImplementedError(
                f"repository {self.name} does not support retrieving the parent "
                "revision"
            )

        return self._getparentrevision(self.path, revision)
