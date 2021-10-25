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
    """A repository."""

    name: str
    path: Path
    revision: Optional[Revision]

    def descend(self, directory: PurePath) -> Package:
        """Return the subrepository located in the given directory."""
        path = self.path.joinpath(*directory.parts)
        return Package(
            directory.name,
            Path(filesystem=PathFilesystem(path)),
            self.revision,
        )
