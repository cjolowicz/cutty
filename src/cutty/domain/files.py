"""File abstraction."""
import abc
import enum
from dataclasses import dataclass

from cutty.filesystem.pure import PurePath


class Mode(enum.Flag):
    """File mode."""

    DEFAULT = 0
    EXECUTABLE = enum.auto()


class File(abc.ABC):
    """File abstraction."""

    @property
    @abc.abstractmethod
    def path(self) -> PurePath:
        """Return the file path."""

    @property
    @abc.abstractmethod
    def mode(self) -> Mode:
        """Return the file mode."""

    @abc.abstractmethod
    def read(self) -> str:
        """Return the file contents."""


@dataclass(frozen=True)
class Buffer(File):
    """A file in memory."""

    _path: PurePath
    _mode: Mode
    _blob: str

    @property
    def path(self) -> PurePath:
        """Return the file path."""
        return self._path

    @property
    def mode(self) -> Mode:
        """Return the file mode."""
        return self._mode

    def read(self) -> str:
        """Return the file contents."""
        return self._blob


class FileStorage(abc.ABC):
    """Any store for files."""

    @abc.abstractmethod
    def store(self, file: File) -> None:
        """Commit a file to storage."""
