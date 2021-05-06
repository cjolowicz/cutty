"""Disk-based file storage."""
from __future__ import annotations

import enum
import functools
import pathlib
import tempfile
from collections.abc import Iterator

from cutty.compat.contextlib import contextmanager
from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.files import SymbolicLink
from cutty.filestorage.domain.storage import FileStore


class FileExistsPolicy(enum.Enum):
    """What to do when a file already exists."""

    RAISE = enum.auto()
    OVERWRITE = enum.auto()
    SKIP = enum.auto()


def storefile(
    file: File,
    *,
    root: pathlib.Path,
    fileexists: FileExistsPolicy,
) -> None:
    """Store the file in a directory on disk."""
    path = root.joinpath(*file.path.parts)

    if path.exists():
        if fileexists is FileExistsPolicy.RAISE:
            raise FileExistsError(f"{path} already exists")

        if fileexists is FileExistsPolicy.SKIP:
            return

    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(file, RegularFile):
        path.write_bytes(file.blob)
        if isinstance(file, Executable):
            path.chmod(path.stat().st_mode | 0o111)

    elif isinstance(file, SymbolicLink):
        target = pathlib.Path(*file.target.parts)
        path.symlink_to(target)

    else:
        raise TypeError(f"cannot store file of type {type(file)}")


@contextmanager
def diskfilestorage(
    root: pathlib.Path,
    *,
    fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
) -> Iterator[FileStore]:
    """Disk-based store for files."""
    yield functools.partial(storefile, root=root, fileexists=fileexists)


@contextmanager
def temporarydiskfilestorage(
    *,
    fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
) -> Iterator[FileStore]:
    """Temporary disk-based store for files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = pathlib.Path(tmpdir)
        with diskfilestorage(root, fileexists=fileexists) as storefile:
            yield storefile
