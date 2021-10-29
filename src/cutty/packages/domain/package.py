"""Package."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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

    @property
    def tree(self) -> Path:
        """."""
        return self.path

    def descend(self, directory: PurePath) -> Package:
        """Return the subpackage located in the given directory."""
        path = self.path.joinpath(*directory.parts)
        return Package(
            directory.name,
            Path(filesystem=PathFilesystem(path)),
            self.revision,
        )
