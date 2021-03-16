"""Filesystem implementation based on pathlib."""
import os
import pathlib
from collections.abc import Iterator

from cutty.domain.filesystem import Access
from cutty.domain.filesystem import Filesystem
from cutty.domain.filesystem import Path


def _fromaccess(access: Access) -> int:
    mapping = {
        Access.READ: os.R_OK,
        Access.WRITE: os.W_OK,
        Access.EXECUTE: os.X_OK,
    }
    return sum(mapping[flag] for flag in access)


class DiskFilesystem(Filesystem):
    """Disk filesystem."""

    def __init__(self, root: pathlib.Path) -> None:
        """Inititalize."""
        self._root = root.resolve(strict=True)

    def resolve(self, path: Path) -> pathlib.Path:
        """Resolve the given path."""
        resolved = self._root.joinpath(*path.parts).resolve()
        resolved.relative_to(self._root)
        return resolved

    def is_dir(self, path: Path) -> bool:
        """Return True if this is a directory."""
        return self.resolve(path).is_dir()

    def iterdir(self, path: Path) -> Iterator[Path]:
        """Iterate over the files in this directory."""
        for child in self.resolve(path).iterdir():
            child = child.relative_to(self._root)
            yield Path(*child.parts)

    def is_file(self, path: Path) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        return self.resolve(path).is_file()

    def read_text(self, path: Path) -> str:
        """Return the contents of this file."""
        return self.resolve(path).read_text()

    def is_symlink(self, path: Path) -> bool:
        """Return True if this is a symbolic link."""
        resolved = self.resolve(path.parent) / path.name
        return resolved.is_symlink()

    def readlink(self, path: Path) -> Path:
        """Return the target of a symbolic link."""
        resolved = self.resolve(path.parent) / path.name
        target = resolved.readlink()
        return Path(*target.parts)

    def access(self, path: Path, mode: Access) -> bool:
        """Return True if the user can access the path."""
        return os.access(self.resolve(path), _fromaccess(mode))

    def eq(self, path: Path, other: Path) -> bool:
        """Return True if the paths are considered equal."""
        return pathlib.Path(*path.parts) == pathlib.Path(*other.parts)

    def lt(self, path: Path, other: Path) -> bool:
        """Return True if the path is less than the other path."""
        return pathlib.Path(*path.parts) < pathlib.Path(*other.parts)
