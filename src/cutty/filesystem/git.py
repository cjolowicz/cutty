"""Git-based filesystem using libgit2."""
import functools
import operator
import pathlib
from collections.abc import Iterator

import pygit2

from cutty.filesystem.base import Access
from cutty.filesystem.base import Filesystem
from cutty.filesystem.pure import PurePath


class GitFilesystem(Filesystem):
    """Git-based filesystem."""

    def __init__(self, repository: pathlib.Path, ref: str = "HEAD") -> None:
        """Inititalize."""
        self.tree = pygit2.Repository(repository).revparse_single(ref).peel(pygit2.Tree)

    def resolve(self, path: PurePath) -> pygit2.Object:
        """Resolve the given path."""
        return functools.reduce(operator.truediv, path.parts, self.tree)

    def is_dir(self, path: PurePath) -> bool:
        """Return True if this is a directory."""
        return isinstance(self.resolve(path), pygit2.Tree)

    def iterdir(self, path: PurePath) -> Iterator[PurePath]:
        """Iterate over the files in this directory."""
        tree = self.resolve(path)
        assert isinstance(tree, pygit2.Tree)  # noqa: S101
        for entry in tree:
            yield path / entry.name

    def is_file(self, path: PurePath) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        return isinstance(self.resolve(path), pygit2.Blob)

    def read_text(self, path: PurePath) -> str:
        """Return the contents of this file."""
        blob = self.resolve(path)
        assert isinstance(blob, pygit2.Blob)  # noqa: S101
        text: str = blob.data.decode()
        return text

    def is_symlink(self, path: PurePath) -> bool:
        """Return True if this is a symbolic link."""
        blob = self.resolve(path)
        return (
            isinstance(blob, pygit2.Blob) and blob.filemode == pygit2.GIT_FILEMODE_LINK
        )

    def readlink(self, path: PurePath) -> PurePath:
        """Return the target of a symbolic link."""
        target = self.read_text(path)
        return PurePath(*target.split("/"))

    def access(self, path: PurePath, mode: Access) -> bool:
        """Return True if the user can access the path."""
        return (
            Access.EXECUTE not in mode
            or self.resolve(path).filemode == pygit2.GIT_FILEMODE_BLOB_EXECUTABLE
        )
