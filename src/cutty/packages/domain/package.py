"""Package."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.pathfs import PathFilesystem
from cutty.filesystems.domain.purepath import PurePath
from cutty.packages.domain.revisions import Revision


@dataclass
class Package:
    """A package."""

    name: str
    path: Path
    revision: Optional[Revision]

    def descend(self, directory: PurePath) -> Package:
        """Return the subpackage located in the given directory."""
        path = self.path.joinpath(*directory.parts)
        return Package(
            directory.name,
            Path(filesystem=PathFilesystem(path)),
            self.revision,
        )


@dataclass
class PackageRepository:
    """A package repository."""

    package: Package

    @contextmanager
    def get(self, revision: Optional[Revision] = None) -> Iterator[Package]:
        """Retrieve the package with the given revision."""
        yield self.package
