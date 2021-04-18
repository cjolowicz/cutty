"""Disk-based filesystem implementation using pathlib."""
import os
import pathlib
from collections.abc import Iterator

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.purepath import PurePath


def _fromaccess(access: Access) -> int:
    mapping = {
        Access.READ: os.R_OK,
        Access.WRITE: os.W_OK,
        Access.EXECUTE: os.X_OK,
    }
    return sum(
        [mapping[flag] for flag in Access if flag and flag in access],
        start=os.F_OK,
    )


class DiskFilesystem(Filesystem):
    """Disk filesystem."""

    def __init__(self, root: pathlib.Path) -> None:
        """Inititalize."""
        self._root = root.resolve(strict=True)

    def resolve(self, path: PurePath) -> pathlib.Path:
        """Resolve the given path."""
        resolved = self._root.joinpath(*path.parts).resolve()
        resolved.relative_to(self._root)
        return resolved

    def is_dir(self, path: PurePath) -> bool:
        """Return True if this is a directory."""
        return self.resolve(path).is_dir()

    def iterdir(self, path: PurePath) -> Iterator[str]:
        """Iterate over the files in this directory."""
        for child in self.resolve(path).iterdir():
            child = child.relative_to(self._root)
            yield child.name

    def is_file(self, path: PurePath) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        return self.resolve(path).is_file()

    def read_bytes(self, path: PurePath) -> bytes:
        """Return the contents of this file."""
        return self.resolve(path).read_bytes()

    def read_text(self, path: PurePath) -> str:
        """Return the contents of this file."""
        return self.resolve(path).read_text()

    def is_symlink(self, path: PurePath) -> bool:
        """Return True if this is a symbolic link."""
        resolved = self.resolve(path.parent) / path.name
        return resolved.is_symlink()

    def readlink(self, path: PurePath) -> PurePath:
        """Return the target of a symbolic link."""
        resolved = self.resolve(path.parent) / path.name
        target = resolved.readlink()
        return PurePath(*target.parts)

    def access(self, path: PurePath, mode: Access) -> bool:
        """Return True if the user can access the path."""
        return os.access(self.resolve(path), _fromaccess(mode))

    def eq(self, path: PurePath, other: PurePath) -> bool:
        """Return True if the paths are considered equal."""
        return pathlib.Path(*path.parts) == pathlib.Path(*other.parts)

    def lt(self, path: PurePath, other: PurePath) -> bool:
        """Return True if the path is less than the other path."""
        return pathlib.Path(*path.parts) < pathlib.Path(*other.parts)
