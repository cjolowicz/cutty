"""File abstraction."""
from __future__ import annotations

import enum
from dataclasses import dataclass

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath


class Mode(enum.Flag):
    """File mode."""

    DEFAULT = 0
    EXECUTABLE = enum.auto()


@dataclass(frozen=True)
class File:
    """A file in memory."""

    path: PurePath
    mode: Mode
    blob: bytes

    @classmethod
    def load(cls, path: Path) -> File:
        """Load file from path."""
        blob = path.read_bytes()
        mode = Mode.EXECUTABLE if path.access(Access.EXECUTE) else Mode.DEFAULT
        return cls(path, mode, blob)
