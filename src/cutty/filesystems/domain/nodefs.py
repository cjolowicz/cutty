"""Default filesystem implementation based on nodes."""
from __future__ import annotations

import abc
import functools
from collections.abc import Iterator

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.purepath import PurePath


class FilesystemNode(abc.ABC):
    """A node in the filesystem."""

    @abc.abstractmethod
    def is_dir(self) -> bool:
        """Return True if the node is a directory."""

    @abc.abstractmethod
    def is_file(self) -> bool:
        """Return True if the node is a regular file."""

    @abc.abstractmethod
    def is_symlink(self) -> bool:
        """Return True if the node is a symbolic link."""

    @abc.abstractmethod
    def read_bytes(self) -> bytes:
        """Return the file contents."""

    @abc.abstractmethod
    def read_text(self) -> str:
        """Return the file contents."""

    @abc.abstractmethod
    def readlink(self) -> PurePath:
        """Return the link target."""

    @abc.abstractmethod
    def iterdir(self) -> Iterator[str]:
        """Iterate over the directory entries."""

    @abc.abstractmethod
    def __truediv__(self, entry: str) -> FilesystemNode:
        """Return the given directory entry."""

    @abc.abstractmethod
    def access(self, mode: Access) -> bool:
        """Return True if the user can access the node."""


class InvalidArgumentError(Exception):
    """The filesystem operation received an invalid argument."""


class NodeFilesystem(Filesystem):
    """A partial filesystem implementation based on nodes."""

    root: FilesystemNode

    @functools.cache
    def lookup(self, path: PurePath) -> FilesystemNode:
        """Return the filesystem node located at the given path."""
        originalpath = path
        nodes = [self.root]

        def _lookup(path: PurePath) -> FilesystemNode:
            """Return the filesystem node for the given path."""
            for part in path.parts:
                if not nodes[-1].is_dir():
                    raise NotADirectoryError(f"not a directory: {path}")

                if part == ".":
                    continue

                if part == "..":
                    if len(nodes) > 1:
                        nodes.pop()
                    continue  # pragma: no cover

                node = self._lookup_entry(nodes[-1], part, path=originalpath)

                if node.is_symlink():
                    target = node.readlink()
                    node = _lookup(target)

                nodes.append(node)

            return nodes[-1]

        return _lookup(path)

    @classmethod
    def _lookup_entry(
        cls, node: FilesystemNode, entry: str, *, path: PurePath
    ) -> FilesystemNode:
        """Lookup a directory entry."""
        try:
            return node / entry
        except FileNotFoundError:
            raise FileNotFoundError(f"file not found: {path}")

    def _lookup_symlink(self, path: PurePath) -> FilesystemNode:
        """Lookup the path without resolving the final path component."""
        parent = self.lookup(path.parent)

        if not parent.is_dir():
            raise NotADirectoryError(f"not a directory: {path}")

        return self._lookup_entry(parent, path.name, path=path)

    def is_dir(self, path: PurePath) -> bool:
        """Return True if this is a directory."""
        try:
            node = self.lookup(path)
        except (FileNotFoundError, NotADirectoryError):
            return False
        else:
            return node.is_dir()

    def iterdir(self, path: PurePath) -> Iterator[str]:
        """Iterate over the files in this directory."""
        node = self.lookup(path)

        if not node.is_dir():
            raise NotADirectoryError(f"not a directory: {path}")

        yield from node.iterdir()

    def is_file(self, path: PurePath) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        try:
            node = self.lookup(path)
        except (FileNotFoundError, NotADirectoryError):
            return False
        else:
            return node.is_file()

    def read_bytes(self, path: PurePath) -> bytes:
        """Return the contents of this file."""
        node = self.lookup(path)

        if node.is_dir():
            raise IsADirectoryError(f"is a directory: {path}")

        return node.read_bytes()

    def read_text(self, path: PurePath) -> str:
        """Return the contents of this file."""
        node = self.lookup(path)

        if node.is_dir():
            raise IsADirectoryError(f"is a directory: {path}")

        return node.read_text()

    def is_symlink(self, path: PurePath) -> bool:
        """Return True if this is a symbolic link."""
        try:
            node = self._lookup_symlink(path)
        except (FileNotFoundError, NotADirectoryError):
            return False
        else:
            return node.is_symlink()

    def readlink(self, path: PurePath) -> PurePath:
        """Return the target of a symbolic link."""
        node = self._lookup_symlink(path)

        if node.is_dir():
            raise IsADirectoryError(f"is a directory: {path}")

        if not node.is_symlink():
            raise InvalidArgumentError(f"not a symbolic file: {path}")

        return node.readlink()

    def access(self, path: PurePath, mode: Access) -> bool:
        """Return True if the user can access the path."""
        try:
            node = self.lookup(path)
        except (FileNotFoundError, NotADirectoryError):
            return False
        else:
            return node.access(mode)
