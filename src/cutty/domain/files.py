"""File abstraction."""
import enum
from collections.abc import Callable
from collections.abc import Iterator
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


def walkfiles(path: Path) -> Iterator[Path]:
    """Iterate over the files under the path."""
    if path.is_file():
        yield path
    elif path.is_dir():
        for entry in path.iterdir():
            yield from walkfiles(entry)
    else:  # pragma: no cover
        raise RuntimeError(f"{path}: not a regular file or directory")
