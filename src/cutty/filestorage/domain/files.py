"""Files."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TypeVar

from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath


_FileT = TypeVar("_FileT", bound="File")


@dataclass(frozen=True)
class File:
    """A file."""

    path: PurePath

    def withpath(self: _FileT, path: PurePath) -> _FileT:
        """Return a copy of this file with the specified path."""
        return dataclasses.replace(self, path=path)


@dataclass(frozen=True)
class RegularFile(File):
    """A regular file."""

    blob: bytes


@dataclass(frozen=True)
class Executable(RegularFile):
    """An executable file."""


@dataclass(frozen=True)
class SymbolicLink(File):
    """A symbolic link."""

    target: PurePath


def loadfile(
    path: Path,
    *,
    follow_symlinks: bool = True,
) -> File:
    """Load file from path."""
    if not follow_symlinks and path.is_symlink():
        target = path.readlink()
        return SymbolicLink(path, target)

    if path.is_file():
        cls = Executable if path.access(Access.EXECUTE) else RegularFile
        return cls(path, path.read_bytes())

    message = (
        "broken symlink"
        if path.is_symlink()
        else "directory"
        if path.is_dir()
        else "special file"
        if path.access()
        else "no such file"
    )
    raise RuntimeError(f"{path}: {message}")
