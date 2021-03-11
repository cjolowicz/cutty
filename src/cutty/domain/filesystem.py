"""Filesystem abstraction."""
import abc
import enum
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from typing import TypeVar


class EmptyPathComponent(Exception):
    """The rendered path has an empty component."""


class InvalidPathComponent(Exception):
    """The rendered path has an invalid component."""


PathT = TypeVar("PathT", bound="Path")


@dataclass
class Path:
    """Location in a filesystem."""

    parts: tuple[str, ...]

    def __init__(self, *parts: str) -> None:
        """Initialize."""
        for part in parts:
            if not part:
                raise EmptyPathComponent(parts, part)

            if "/" in part or "\\" in part or part == "." or part == "..":
                raise InvalidPathComponent(parts, part)

        object.__setattr__(self, "parts", parts)

    def _copy(self: PathT, path: Path) -> PathT:
        """Create a copy of the given path."""
        return self.__class__(*path.parts)

    def __str__(self) -> str:
        """Return a readable representation."""
        return "/".join(self.parts)

    def __truediv__(self: PathT, part: str) -> PathT:
        """Return a path with the part appended."""
        return self.joinpath(part)

    @property
    def name(self) -> str:
        """The final path component, if any."""
        return self.parts[-1] if self.parts else ""

    @property
    def stem(self) -> str:
        """The final path component, minus its last suffix."""
        name = self.name
        index = name.rfind(".")
        return name[:index] if 0 < index < len(name) - 1 else name

    @property
    def parent(self: PathT) -> PathT:
        """Return the parent of this path."""
        if not self.parts:
            return self

        path = Path(*self.parts[:-1])
        return self._copy(path)

    def joinpath(self: PathT, *parts: str) -> PathT:
        """Return a path with the parts appended."""
        path = Path(*self.parts, *parts)
        return self._copy(path)


class Access(enum.Flag):
    """File access mode."""

    DEFAULT = 0
    EXECUTE = enum.auto()
    WRITE = enum.auto()
    READ = enum.auto()


class Filesystem(abc.ABC):
    """A filesystem abstraction."""

    @property
    def root(self) -> FilesystemPath:
        """Return the path at the root of the filesystem."""
        return FilesystemPath(filesystem=self)

    @abc.abstractmethod
    def iterdir(self, path: Path) -> Iterator[Path]:
        """Iterate over the files in this directory."""

    @abc.abstractmethod
    def read_text(self, path: Path) -> str:
        """Return the contents of this file."""

    @abc.abstractmethod
    def is_file(self, path: Path) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""

    @abc.abstractmethod
    def is_dir(self, path: Path) -> bool:
        """Return True if this is a directory."""

    @abc.abstractmethod
    def is_symlink(self, path: Path) -> bool:
        """Return True if this is a symbolic link."""

    @abc.abstractmethod
    def access(self, path: Path, mode: Access) -> bool:
        """Return True if the user can access the path."""

    def eq(self, path: Path, other: Path) -> bool:
        """Return True if the paths are considered equal."""
        return path.parts == other.parts

    def lt(self, path: Path, other: Path) -> bool:
        """Return True if the path is less than the other path."""
        return path.parts < other.parts


class FilesystemPath(Path):
    """Location in a filesystem, with methods for accessing the filesystem."""

    _filesystem: Filesystem

    def __init__(self, *parts: str, filesystem: Filesystem) -> None:
        """Initialize."""
        super().__init__(*parts)
        object.__setattr__(self, "_filesystem", filesystem)

    def _copy(self, path: Path) -> FilesystemPath:
        """Create a copy of the given path."""
        return FilesystemPath(*path.parts, filesystem=self._filesystem)

    def iterdir(self) -> Iterator[FilesystemPath]:
        """Iterate over the files in this directory."""
        for path in self._filesystem.iterdir(self):
            yield self._copy(path)

    def read_text(self) -> str:
        """Return the contents of this file."""
        return self._filesystem.read_text(self)

    def is_file(self) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        return self._filesystem.is_file(self)

    def is_dir(self) -> bool:
        """Return True if this is a directory."""
        return self._filesystem.is_dir(self)

    def is_symlink(self) -> bool:
        """Return True if this is a symbolic link."""
        return self._filesystem.is_symlink(self)

    def access(self, mode: Access) -> bool:
        """Return True if the user can access the path."""
        return self._filesystem.access(self, mode)

    def __hash__(self) -> int:
        """Return the hash value of the path."""
        return hash((self.parts, self._filesystem))

    def __eq__(self, other: Any) -> bool:
        """Return True if the paths are equal."""
        if not isinstance(other, FilesystemPath):
            return NotImplemented
        return self._filesystem is other._filesystem and self._filesystem.eq(
            self, other
        )

    def __lt__(self, other: Any) -> bool:
        """Return True if the path is less than the other path."""
        if not isinstance(other, FilesystemPath):
            return NotImplemented
        if self._filesystem is not other._filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return self._filesystem.lt(self, other)

    def __gt__(self, other: Any) -> bool:
        """Return True if the path is greater than the other path."""
        if not isinstance(other, FilesystemPath):
            return NotImplemented
        if self._filesystem is not other._filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return self._filesystem.lt(other, self)

    def __le__(self, other: Any) -> bool:
        """Return True if the path is less than or equal to the other path."""
        if not isinstance(other, FilesystemPath):
            return NotImplemented
        if self._filesystem is not other._filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return not self._filesystem.lt(other, self)

    def __ge__(self, other: Any) -> bool:
        """Return True if the path is greater than or equal to the other path."""
        if not isinstance(other, FilesystemPath):
            return NotImplemented
        if self._filesystem is not other._filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return not self._filesystem.lt(self, other)
