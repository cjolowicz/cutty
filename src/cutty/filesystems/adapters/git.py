"""Git-based filesystem using libgit2."""
import functools
import operator
import pathlib
from collections.abc import Iterator

import pygit2

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.purepath import PurePath


class GitFilesystem(Filesystem):
    """Git-based filesystem."""

    def __init__(self, repository: pathlib.Path, ref: str = "HEAD") -> None:
        """Inititalize."""
        self.tree = pygit2.Repository(repository).revparse_single(ref).peel(pygit2.Tree)

    def resolve(self, path: PurePath) -> pygit2.Object:
        """Resolve the given path."""
        try:
            return functools.reduce(operator.truediv, path.parts, self.tree)
        except KeyError:
            raise FileNotFoundError(f"file not found: {path}")

    def is_dir(self, path: PurePath) -> bool:
        """Return True if this is a directory."""
        try:
            tree = self.resolve(path)
        except FileNotFoundError:
            return False
        else:
            return isinstance(tree, pygit2.Tree)

    def iterdir(self, path: PurePath) -> Iterator[PurePath]:
        """Iterate over the files in this directory."""
        tree = self.resolve(path)
        if not isinstance(tree, pygit2.Tree):
            raise NotADirectoryError(f"not a directory: {path}")

        for entry in tree:
            yield path / entry.name

    def is_file(self, path: PurePath) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        try:
            blob = self.resolve(path)
        except FileNotFoundError:
            return False
        else:
            return isinstance(blob, pygit2.Blob)

    def read_text(self, path: PurePath) -> str:
        """Return the contents of this file."""
        blob = self.resolve(path)
        if isinstance(blob, pygit2.Tree):
            raise IsADirectoryError(f"is a directory: {path}")

        if not isinstance(blob, pygit2.Blob):  # pragma: no cover
            raise RuntimeError(f"unexpected object type: {path} ({blob})")

        text: str = blob.data.decode()
        return text

    def is_symlink(self, path: PurePath) -> bool:
        """Return True if this is a symbolic link."""
        try:
            blob = self.resolve(path)
        except FileNotFoundError:
            return False
        else:
            return (
                isinstance(blob, pygit2.Blob)
                and blob.filemode == pygit2.GIT_FILEMODE_LINK
            )

    def readlink(self, path: PurePath) -> PurePath:
        """Return the target of a symbolic link."""
        blob = self.resolve(path)
        if isinstance(blob, pygit2.Tree):
            raise IsADirectoryError(f"is a directory: {path}")

        if not (
            isinstance(blob, pygit2.Blob) and blob.filemode == pygit2.GIT_FILEMODE_LINK
        ):
            raise RuntimeError(f"not a symlink: {path}")

        target: str = blob.data.decode(errors="surrogateescape")

        # TODO: Parse the path.
        # TODO: Handle absolute paths in some way.
        return PurePath(*target.split("/"))

    def access(self, path: PurePath, mode: Access) -> bool:
        """Return True if the user can access the path."""
        try:
            obj = self.resolve(path)
        except FileNotFoundError:
            return False
        else:
            return (
                Access.EXECUTE not in mode
                or obj.filemode == pygit2.GIT_FILEMODE_BLOB_EXECUTABLE
            )
