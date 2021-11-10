"""Package."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.pathfs import PathFilesystem
from cutty.filesystems.domain.purepath import PurePath
from cutty.packages.domain.revisions import Revision


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


@dataclass
class Package:
    """A package."""

    name: str
    tree: Path
    revision: Optional[Revision] = None
    commit: Optional[str] = None
    message: Optional[str] = None
    author: Optional[str] = None
    authoremail: Optional[str] = None

    @property
    def commit2(self) -> Optional[Commit]:
        """Return the commit metadata."""
        if self.commit is None:
            return None

        assert self.revision is not None  # noqa: S101
        assert self.message is not None  # noqa: S101
        assert self.author is not None  # noqa: S101
        assert self.authoremail is not None  # noqa: S101

        return Commit(
            self.commit,
            self.revision,
            self.message,
            Author(self.author, self.authoremail),
        )

    def descend(self, directory: PurePath) -> Package:
        """Return the subpackage located in the given directory."""
        tree = self.tree.joinpath(*directory.parts)
        tree = Path(filesystem=PathFilesystem(tree))

        return Package(
            directory.name,
            tree,
            self.revision,
            self.commit,
            self.message,
            self.author,
            self.authoremail,
        )
