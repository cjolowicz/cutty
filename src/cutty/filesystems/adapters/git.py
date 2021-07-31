"""Git-based filesystem using libgit2."""
import pathlib
from collections.abc import Iterator

import pygit2

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.nodefs import FilesystemNode
from cutty.filesystems.domain.nodefs import NodeFilesystem
from cutty.filesystems.domain.purepath import PurePath


class GitFilesystemNode(FilesystemNode):
    """A node in a git filesystem."""

    def __init__(self, node: pygit2.Object) -> None:
        """Initialize."""
        self.node = node

    def is_dir(self) -> bool:
        """Return True if the node is a directory."""
        return isinstance(self.node, pygit2.Tree)

    def is_file(self) -> bool:
        """Return True if the node is a regular file."""
        return (
            isinstance(self.node, pygit2.Blob)
            and self.node.filemode != pygit2.GIT_FILEMODE_LINK
        )

    def is_symlink(self) -> bool:
        """Return True if the node is a symbolic link."""
        return (
            isinstance(self.node, pygit2.Blob)
            and self.node.filemode == pygit2.GIT_FILEMODE_LINK
        )

    def read_bytes(self) -> bytes:
        """Return the file contents."""
        data: bytes = self.node.data
        return data

    def read_text(self) -> str:
        """Return the file contents."""
        return self.read_bytes().decode()

    def readlink(self) -> PurePath:
        """Return the link target."""
        target: str = self.node.data.decode(errors="surrogateescape")
        parts = pathlib.PurePosixPath(target).parts
        return PurePath(*parts)

    def iterdir(self) -> Iterator[str]:
        """Iterate over the directory entries."""
        for entry in self.node:
            yield entry.name

    def __truediv__(self, entry: str) -> FilesystemNode:
        """Return the given directory entry."""
        try:
            return GitFilesystemNode(self.node / entry)
        except KeyError:
            raise FileNotFoundError()

    def access(self, mode: Access) -> bool:
        """Return True if the user can access the node."""
        return (
            Access.EXECUTE not in mode
            or self.node.filemode == pygit2.GIT_FILEMODE_BLOB_EXECUTABLE
        )


class GitFilesystem(NodeFilesystem):
    """Git-based filesystem."""

    def __init__(self, repository: pathlib.Path, ref: str = "HEAD") -> None:
        """Inititalize."""
        repo = pygit2.Repository(repository)
        tree = repo.revparse_single(ref).peel(pygit2.Tree)
        self.root = GitFilesystemNode(tree)
