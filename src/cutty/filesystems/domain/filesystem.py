"""Filesystem abstraction."""
import abc
import enum
from collections.abc import Iterator

from cutty.filesystems.domain.purepath import PurePath


class Access(enum.Flag):
    """File access mode."""

    DEFAULT = 0
    EXECUTE = enum.auto()
    WRITE = enum.auto()
    READ = enum.auto()


class Filesystem(abc.ABC):
    """A filesystem abstraction."""

    @abc.abstractmethod
    def is_dir(self, path: PurePath) -> bool:
        """Return True if this is a directory."""

    @abc.abstractmethod
    def iterdir(self, path: PurePath) -> Iterator[str]:
        """Iterate over the files in this directory."""

    @abc.abstractmethod
    def is_file(self, path: PurePath) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""

    @abc.abstractmethod
    def read_bytes(self, path: PurePath) -> bytes:
        """Return the contents of this file."""

    @abc.abstractmethod
    def read_text(self, path: PurePath) -> str:
        """Return the contents of this file."""

    @abc.abstractmethod
    def is_symlink(self, path: PurePath) -> bool:
        """Return True if this is a symbolic link."""

    @abc.abstractmethod
    def readlink(self, path: PurePath) -> PurePath:
        """Return the target of a symbolic link."""

    @abc.abstractmethod
    def access(self, path: PurePath, mode: Access) -> bool:
        """Return True if the user can access the path."""

    def eq(self, path: PurePath, other: PurePath) -> bool:
        """Return True if the paths are considered equal."""
        return path.parts == other.parts

    def lt(self, path: PurePath, other: PurePath) -> bool:
        """Return True if the path is less than the other path."""
        return path.parts < other.parts
