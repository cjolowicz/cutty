"""File abstraction."""
import enum
from collections.abc import Callable
from dataclasses import dataclass

from cutty.filesystem.base import Access
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


FileStorage = Callable[[File], None]


def loadfile(path: Path) -> File:
    """Load file from path."""
    blob = path.read_text()
    mode = Mode.EXECUTABLE if path.access(Access.EXECUTE) else Mode.DEFAULT
    return File(path, mode, blob)
