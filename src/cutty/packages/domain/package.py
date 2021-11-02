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
    tree: Path
    revision: Optional[Revision]
    commit: Optional[str] = None
    message: Optional[str] = None

    def descend(self, directory: PurePath) -> Package:
        """Return the subpackage located in the given directory."""
        tree = self.tree.joinpath(*directory.parts)
        tree = Path(filesystem=PathFilesystem(tree))

        return Package(directory.name, tree, self.revision, self.commit, self.message)
