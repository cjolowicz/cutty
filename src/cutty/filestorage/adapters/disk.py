"""Disk-based file storage."""
from __future__ import annotations

import enum
import functools
import pathlib
import tempfile
from collections.abc import Callable
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


def storefile(  # noqa: C901
    file: File,
    *,
    root: pathlib.Path,
    fileexists: FileExistsPolicy,
    undo: list[Callable[[], None]],
) -> None:
    """Store the file in a directory on disk."""
    path = root.joinpath(*file.path.parts)
    overwrite = False

    if path.exists():
        if fileexists is FileExistsPolicy.RAISE:
            raise FileExistsError(f"{path} already exists")

        if fileexists is FileExistsPolicy.SKIP:
            return

        overwrite = True

        # Overwriting directories with regular files or symbolic links is not
        # allowed. Neither is overwriting regular files with symbolic links. Let
        # these operations raise their own exceptions. Overwriting a symbolic
        # link with a regular file or another symbolic link requires removing
        # the existing symbolic link beforehand.
        if path.is_symlink():
            path.unlink()

    for parent in reversed(path.parents):
        # A symbolic link in the path whose target is not a directory will
        # result in FileExistsError. XXX Should we guard against symbolic links
        # whose target is a directory here?
        if not parent.is_dir():
            parent.mkdir()
            undo.append(parent.rmdir)

    if isinstance(file, RegularFile):
        path.write_bytes(file.blob)

        if not overwrite:
            undo.append(path.unlink)

        if isinstance(file, Executable):
            path.chmod(path.stat().st_mode | 0o111)

    elif isinstance(file, SymbolicLink):
        target = pathlib.Path(*file.target.parts)
        path.symlink_to(target)

        if not overwrite:
            undo.append(path.unlink)

    else:
        raise TypeError(f"cannot store file of type {type(file)}")


@contextmanager
def diskfilestorage(
    root: pathlib.Path,
    *,
    fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
) -> Iterator[FileStore]:
    """Disk-based store for files."""
    undo: list[Callable[[], None]] = []

    try:
        yield functools.partial(storefile, root=root, fileexists=fileexists, undo=undo)
    except BaseException:
        for action in reversed(undo):
            action()  # if this fails then so be it
        raise


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
