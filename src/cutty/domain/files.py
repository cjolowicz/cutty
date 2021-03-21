"""File abstraction."""
import abc
import enum
from collections.abc import Iterator
from dataclasses import dataclass

from cutty.filesystem.path import Path
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


class FileLoader(abc.ABC):
    """Interface for loading project files for a template."""

    @abc.abstractmethod
    def load(self, path: Path) -> Iterator[File]:
        """Load project files."""


class FileStorage(abc.ABC):
    """Any store for files."""

    @abc.abstractmethod
    def store(self, file: File) -> None:
        """Commit a file to storage."""
