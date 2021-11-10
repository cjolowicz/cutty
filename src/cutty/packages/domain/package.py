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
    _revision: Optional[Revision] = None
    _commit: Optional[str] = None
    _message: Optional[str] = None
    _author: Optional[str] = None
    _authoremail: Optional[str] = None

    @property
    def commit2(self) -> Optional[Commit]:
        """Return the commit metadata."""
        if self._commit is None:
            return None

        assert self._revision is not None  # noqa: S101
        assert self._message is not None  # noqa: S101
        assert self._author is not None  # noqa: S101
        assert self._authoremail is not None  # noqa: S101

        return Commit(
            self._commit,
            self._revision,
            self._message,
            Author(self._author, self._authoremail),
        )

    def descend(self, directory: PurePath) -> Package:
        """Return the subpackage located in the given directory."""
        tree = self.tree.joinpath(*directory.parts)
        tree = Path(filesystem=PathFilesystem(tree))

        return Package(
            directory.name,
            tree,
            self._revision,
            self._commit,
            self._message,
            self._author,
            self._authoremail,
        )
