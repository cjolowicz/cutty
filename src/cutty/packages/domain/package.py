"""Package."""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional

from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.pathfs import PathFilesystem
from cutty.filesystems.domain.purepath import PurePath


@dataclass
class Author:
    """The commit author."""

    name: str
    email: str


@dataclass
class Commit:
    """A commit in a versioned repository."""

    id: str
    revision: str
    message: str
    author: Author
    date: datetime.datetime


@dataclass
class Package:
    """A package."""

    name: str
    tree: Path
    commit: Optional[Commit] = None

    def descend(self, directory: PurePath) -> Package:
        """Return the subpackage located in the given directory."""
        tree = self.tree.joinpath(*directory.parts)
        tree = Path(filesystem=PathFilesystem(tree))

        return Package(directory.name, tree, self.commit)
