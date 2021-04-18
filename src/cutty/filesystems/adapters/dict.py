"""Dictionary-based filesystem for your pocket."""
from collections.abc import Iterator
from typing import Any
from typing import cast

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.nodefs import FilesystemNode
from cutty.filesystems.domain.nodefs import NodeFilesystem
from cutty.filesystems.domain.purepath import PurePath


class DictFilesystemNode(FilesystemNode):
    """A node in a dict filesystem."""

    def __init__(self, node: Any) -> None:
        """Initialize."""
        self.node = node

    def is_dir(self) -> bool:
        """Return True if the node is a directory."""
        return isinstance(self.node, dict)

    def is_file(self) -> bool:
        """Return True if the node is a regular file."""
        return isinstance(self.node, str)

    def is_symlink(self) -> bool:
        """Return True if the node is a symbolic link."""
        return isinstance(self.node, PurePath)

    def read_bytes(self) -> bytes:
        """Return the file contents."""
        return self.read_text().encode()

    def read_text(self) -> str:
        """Return the file contents."""
        return cast(str, self.node)

    def readlink(self) -> PurePath:
        """Return the link target."""
        return cast(PurePath, self.node)

    def iterdir(self) -> Iterator[str]:
        """Iterate over the directory entries."""
        node: dict[str, Any] = self.node
        return iter(node.keys())

    def __truediv__(self, entry: str) -> FilesystemNode:
        """Return the given directory entry."""
        try:
            return DictFilesystemNode(self.node[entry])
        except KeyError:
            raise FileNotFoundError()

    def access(self, mode: Access) -> bool:
        """Return True if the user can access the node."""
        return Access.EXECUTE not in mode or self.is_dir()


class DictFilesystem(NodeFilesystem):
    """Dictionary-based filesystem for your pocket."""

    def __init__(self, tree: dict[str, Any]) -> None:
        """Initialize."""
        self.root = DictFilesystemNode(tree)
