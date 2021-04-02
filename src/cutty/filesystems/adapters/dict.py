"""Dictionary-based filesystem for your pocket."""
from collections.abc import Iterator
from typing import Any

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.purepath import PurePath


class DictFilesystem(Filesystem):
    """Dictionary-based filesystem for your pocket."""

    def __init__(self, tree: Any) -> None:
        """Initialize."""
        # Node = str | PurePath | dict[str, Node]
        # Tree = dict[str, Node]
        self.tree = tree

    def lookup(self, path: PurePath) -> Any:
        """Return the filesystem node at the given path."""
        # Remember the original path for error messages.
        originalpath = path

        # Traversed filesystem nodes, starting at the root.
        nodes = [self.tree]

        def _lookup(path: PurePath) -> Any:
            """Return the filesystem node for the given path."""
            for part in path.parts:
                if part == ".":
                    continue

                if part == "..":
                    if len(nodes) > 1:
                        nodes.pop()
                    continue  # pragma: no cover

                try:
                    node = nodes[-1][part]
                except KeyError:
                    raise FileNotFoundError(f"file not found: {originalpath}")

                if isinstance(node, PurePath):
                    node = _lookup(node)

                nodes.append(node)

            return nodes[-1]

        return _lookup(path)

    def is_dir(self, path: PurePath) -> bool:
        """Return True if this is a directory."""
        try:
            entry = self.lookup(path)
        except FileNotFoundError:
            return False
        return isinstance(entry, dict)

    def iterdir(self, path: PurePath) -> Iterator[PurePath]:
        """Iterate over the files in this directory."""
        entry = self.lookup(path)
        if not isinstance(entry, dict):
            raise NotADirectoryError(f"not a directory: {path}")
        for key in entry:
            yield path / key

    def is_file(self, path: PurePath) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        try:
            entry = self.lookup(path)
        except FileNotFoundError:
            return False
        return isinstance(entry, str)

    def read_text(self, path: PurePath) -> str:
        """Return the contents of this file."""
        entry = self.lookup(path)
        if isinstance(entry, dict):
            raise IsADirectoryError(f"is a directory: {path}")
        assert isinstance(entry, str)  # noqa: S101
        return entry

    def is_symlink(self, path: PurePath) -> bool:
        """Return True if this is a symbolic link."""
        try:
            entry = self.lookup(path.parent)[path.name]
        except (FileNotFoundError, KeyError):
            return False
        return isinstance(entry, PurePath)

    def readlink(self, path: PurePath) -> PurePath:
        """Return the target of a symbolic link."""
        entry = self.lookup(path.parent)[path.name]
        if not isinstance(entry, PurePath):
            raise ValueError("not a symbolic link")
        return entry

    def access(self, path: PurePath, mode: Access) -> bool:
        """Return True if the user can access the path."""
        try:
            self.lookup(path)
        except FileNotFoundError:
            return False
        if mode & Access.EXECUTE:
            return self.is_dir(path)
        return True
