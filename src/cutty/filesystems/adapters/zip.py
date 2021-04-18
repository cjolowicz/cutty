"""Filesystem implementation for ZIP archives using zipfile."""
import pathlib
import stat
import zipfile
from collections.abc import Iterator

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.nodefs import FilesystemNode
from cutty.filesystems.domain.nodefs import NodeFilesystem
from cutty.filesystems.domain.purepath import PurePath


def _fromaccess(access: Access) -> int:
    mapping = {
        Access.READ: stat.S_IRUSR,
        Access.WRITE: stat.S_IWUSR,
        Access.EXECUTE: stat.S_IXUSR,
    }
    return sum([mapping[flag] for flag in Access if flag and flag in access])


def _getfilemode(zippath: zipfile.Path) -> int:
    info: zipfile.ZipInfo
    info = zippath.root.getinfo(zippath.at)  # type: ignore[attr-defined]
    return info.external_attr >> 16


class ZipFilesystemNode(FilesystemNode):
    """A node in a ZIP filesystem."""

    def __init__(self, node: zipfile.Path) -> None:
        """Initialize."""
        self.node = node

    def is_dir(self) -> bool:
        """Return True if the node is a directory."""
        return self.node.is_dir()

    def is_file(self) -> bool:
        """Return True if the node is a regular file."""
        return self.node.is_file()

    def is_symlink(self) -> bool:
        """Return True if the node is a symbolic link."""
        return False

    def read_bytes(self) -> bytes:
        """Return the file contents."""
        return self.node.read_bytes()

    def read_text(self) -> str:
        """Return the file contents."""
        return self.node.read_text()

    def readlink(self) -> PurePath:
        """Return the link target."""
        raise NotImplementedError()  # pragma: no cover

    def iterdir(self) -> Iterator[str]:
        """Iterate over the directory entries."""
        for entry in self.node.iterdir():
            yield entry.name

    def __truediv__(self, entry: str) -> FilesystemNode:
        """Return the given directory entry."""
        node = self.node / entry

        if not node.exists():
            raise FileNotFoundError()

        return ZipFilesystemNode(node)

    def access(self, mode: Access) -> bool:
        """Return True if the user can access the node."""
        return not mode or bool(_getfilemode(self.node) & _fromaccess(mode))


class ZipFilesystem(NodeFilesystem):
    """ZIP filesystem."""

    def __init__(self, path: pathlib.Path) -> None:
        """Inititalize."""
        node = zipfile.Path(path)
        self.root = ZipFilesystemNode(node)
