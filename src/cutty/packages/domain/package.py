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

    @classmethod
    def create(
        cls,
        _revision: Optional[Revision] = None,
        _commit: Optional[str] = None,
        _message: Optional[str] = None,
        _author: Optional[str] = None,
        _authoremail: Optional[str] = None,
    ) -> Optional[Commit]:
        """Create a commit instance."""
        if _commit is None:
            return None

        assert _revision is not None  # noqa: S101
        assert _message is not None  # noqa: S101
        assert _author is not None  # noqa: S101
        assert _authoremail is not None  # noqa: S101

        return cls(_commit, _revision, _message, Author(_author, _authoremail))


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
