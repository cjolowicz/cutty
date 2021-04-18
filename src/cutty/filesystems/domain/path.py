"""Filesystem path."""
from __future__ import annotations

from collections.abc import Iterator

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.purepath import PurePath
from cutty.util.typeguard_ignore import typeguard_ignore


class Path(PurePath):
    """Location in a filesystem, with methods for accessing the filesystem."""

    filesystem: Filesystem

    def __init__(self, *parts: str, filesystem: Filesystem) -> None:
        """Initialize."""
        super().__init__(*parts)
        object.__setattr__(self, "filesystem", filesystem)

    def _withparts(self, *parts: str) -> Path:
        """Create a path with the given parts."""
        return Path(*parts, filesystem=self.filesystem)

    def is_dir(self) -> bool:
        """Return True if this is a directory."""
        return self.filesystem.is_dir(self)

    def iterdir(self) -> Iterator[Path]:
        """Iterate over the files in this directory."""
        for entry in self.filesystem.iterdir(self):
            yield self / entry

    def is_file(self) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        return self.filesystem.is_file(self)

    def read_bytes(self) -> bytes:
        """Return the contents of this file."""
        return self.filesystem.read_bytes(self)

    def read_text(self) -> str:
        """Return the contents of this file."""
        return self.filesystem.read_text(self)

    def is_symlink(self) -> bool:
        """Return True if this is a symbolic link."""
        return self.filesystem.is_symlink(self)

    def readlink(self) -> PurePath:
        """Return the target of a symbolic link."""
        return self.filesystem.readlink(self)

    def access(self, mode: Access = Access.DEFAULT) -> bool:
        """Return True if the user can access the path."""
        return self.filesystem.access(self, mode)

    def __hash__(self) -> int:
        """Return the hash value of the path."""
        return hash((self.parts, self.filesystem))

    @typeguard_ignore
    def __eq__(self, other: object) -> bool:
        """Return True if the paths are equal."""
        if not isinstance(other, Path):
            return NotImplemented
        return self.filesystem is other.filesystem and self.filesystem.eq(self, other)

    @typeguard_ignore
    def __lt__(self, other: object) -> bool:
        """Return True if the path is less than the other path."""
        if not isinstance(other, Path):
            return NotImplemented
        if self.filesystem is not other.filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return self.filesystem.lt(self, other)

    @typeguard_ignore
    def __gt__(self, other: object) -> bool:
        """Return True if the path is greater than the other path."""
        if not isinstance(other, Path):
            return NotImplemented
        if self.filesystem is not other.filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return self.filesystem.lt(other, self)

    @typeguard_ignore
    def __le__(self, other: object) -> bool:
        """Return True if the path is less than or equal to the other path."""
        if not isinstance(other, Path):
            return NotImplemented
        if self.filesystem is not other.filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return not self.filesystem.lt(other, self)

    @typeguard_ignore
    def __ge__(self, other: object) -> bool:
        """Return True if the path is greater than or equal to the other path."""
        if not isinstance(other, Path):
            return NotImplemented
        if self.filesystem is not other.filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return not self.filesystem.lt(self, other)
