"""Filesystem implementation providing a view into another filesystem."""
from collections.abc import Iterator

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.nodefs import FilesystemNode
from cutty.filesystems.domain.nodefs import NodeFilesystem
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath


class PathNode(FilesystemNode):
    """A node in the filesystem."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.path = path

    def is_dir(self) -> bool:
        """Return True if the node is a directory."""
        return self.path.is_dir()

    def is_file(self) -> bool:
        """Return True if the node is a regular file."""
        return self.path.is_file()

    def is_symlink(self) -> bool:
        """Return True if the node is a symbolic link."""
        return self.path.is_symlink()

    def read_bytes(self) -> bytes:
        """Return the file contents."""
        return self.path.read_bytes()

    def read_text(self) -> str:
        """Return the file contents."""
        return self.path.read_text()

    def readlink(self) -> PurePath:
        """Return the link target."""
        return self.path.readlink()

    def iterdir(self) -> Iterator[str]:
        """Iterate over the directory entries."""
        for path in self.path.iterdir():
            yield path.name

    def __truediv__(self, entry: str) -> FilesystemNode:
        """Return the given directory entry."""
        return PathNode(self.path / entry)

    def access(self, mode: Access) -> bool:
        """Return True if the user can access the node."""
        return self.path.access(mode)


class PathFilesystem(NodeFilesystem):
    """Filesystem implementation providing a view into another filesystem."""

    def __init__(self, path: Path) -> None:
        """Inititalize."""
        self.root = PathNode(path)
