"""File abstraction."""
import abc
import enum
from dataclasses import dataclass

from cutty.filesystem.pure import PurePath


class Mode(enum.Flag):
    """File mode."""

    DEFAULT = 0
    EXECUTABLE = enum.auto()


@dataclass(frozen=True)
class File:
    """A file in memory."""

    path: PurePath
    mode: Mode
    blob: str


class FileStorage(abc.ABC):
    """Any store for files."""

    @abc.abstractmethod
    def store(self, file: File) -> None:
        """Commit a file to storage."""
