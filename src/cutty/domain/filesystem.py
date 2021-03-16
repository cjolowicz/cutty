"""Filesystem abstraction."""
import abc
import enum
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TypeVar

from cutty.util.typeguard_ignore import typeguard_ignore


PurePathT = TypeVar("PurePathT", bound="PurePath")


@dataclass
class PurePath:
    """Location in a filesystem."""

    parts: tuple[str, ...]

    def __init__(self, *parts: str) -> None:
        """Initialize."""
        object.__setattr__(self, "parts", parts)

    def _copy(self: PurePathT, path: PurePath) -> PurePathT:
        """Create a copy of the given path."""
        return self.__class__(*path.parts)

    def __str__(self) -> str:
        """Return a readable representation."""
        return "/".join(self.parts)

    def __truediv__(self: PurePathT, part: str) -> PurePathT:
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
    def parent(self: PurePathT) -> PurePathT:
        """Return the parent of this path."""
        if not self.parts:
            return self

        path = PurePath(*self.parts[:-1])
        return self._copy(path)

    def joinpath(self: PurePathT, *parts: str) -> PurePathT:
        """Return a path with the parts appended."""
        path = PurePath(*self.parts, *parts)
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
    def root(self) -> Path:
        """Return the path at the root of the filesystem."""
        return Path(filesystem=self)

    @abc.abstractmethod
    def is_dir(self, path: PurePath) -> bool:
        """Return True if this is a directory."""

    @abc.abstractmethod
    def iterdir(self, path: PurePath) -> Iterator[PurePath]:
        """Iterate over the files in this directory."""

    @abc.abstractmethod
    def is_file(self, path: PurePath) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""

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


class Path(PurePath):
    """Location in a filesystem, with methods for accessing the filesystem."""

    _filesystem: Filesystem

    def __init__(self, *parts: str, filesystem: Filesystem) -> None:
        """Initialize."""
        super().__init__(*parts)
        object.__setattr__(self, "_filesystem", filesystem)

    def _copy(self, path: PurePath) -> Path:
        """Create a copy of the given path."""
        return Path(*path.parts, filesystem=self._filesystem)

    def is_dir(self) -> bool:
        """Return True if this is a directory."""
        return self._filesystem.is_dir(self)

    def iterdir(self) -> Iterator[Path]:
        """Iterate over the files in this directory."""
        for path in self._filesystem.iterdir(self):
            yield self._copy(path)

    def is_file(self) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        return self._filesystem.is_file(self)

    def read_text(self) -> str:
        """Return the contents of this file."""
        return self._filesystem.read_text(self)

    def is_symlink(self) -> bool:
        """Return True if this is a symbolic link."""
        return self._filesystem.is_symlink(self)

    def readlink(self) -> PurePath:
        """Return the target of a symbolic link."""
        return self._filesystem.readlink(self)

    def access(self, mode: Access = Access.DEFAULT) -> bool:
        """Return True if the user can access the path."""
        return self._filesystem.access(self, mode)

    def __hash__(self) -> int:
        """Return the hash value of the path."""
        return hash((self.parts, self._filesystem))

    @typeguard_ignore
    def __eq__(self, other: object) -> bool:
        """Return True if the paths are equal."""
        if not isinstance(other, Path):
            return NotImplemented
        return self._filesystem is other._filesystem and self._filesystem.eq(
            self, other
        )

    @typeguard_ignore
    def __lt__(self, other: object) -> bool:
        """Return True if the path is less than the other path."""
        if not isinstance(other, Path):
            return NotImplemented
        if self._filesystem is not other._filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return self._filesystem.lt(self, other)

    @typeguard_ignore
    def __gt__(self, other: object) -> bool:
        """Return True if the path is greater than the other path."""
        if not isinstance(other, Path):
            return NotImplemented
        if self._filesystem is not other._filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return self._filesystem.lt(other, self)

    @typeguard_ignore
    def __le__(self, other: object) -> bool:
        """Return True if the path is less than or equal to the other path."""
        if not isinstance(other, Path):
            return NotImplemented
        if self._filesystem is not other._filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return not self._filesystem.lt(other, self)

    @typeguard_ignore
    def __ge__(self, other: object) -> bool:
        """Return True if the path is greater than or equal to the other path."""
        if not isinstance(other, Path):
            return NotImplemented
        if self._filesystem is not other._filesystem:
            raise ValueError("cannot compare paths on different filesystems")
        return not self._filesystem.lt(self, other)
