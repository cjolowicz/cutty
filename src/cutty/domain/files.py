"""File abstraction."""
import enum
from collections.abc import Callable
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


FileLoader = Callable[[Path], Iterator[File]]
FileStorage = Callable[[File], None]
