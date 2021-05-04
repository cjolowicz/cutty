"""Files."""
from dataclasses import dataclass

from cutty.filesystems.domain.purepath import PurePath


@dataclass(frozen=True)
class File:
    """A file."""

    path: PurePath


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
