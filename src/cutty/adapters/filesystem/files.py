"""Filesystem implementation of the cutty.domain.files abstractions."""
import os
import pathlib
import tempfile
from collections.abc import Iterator

from cutty.compat.contextlib import contextmanager
from cutty.domain.files import Buffer
from cutty.domain.files import File
from cutty.domain.files import FileStorage
from cutty.domain.files import Mode
from cutty.domain.filesystem import PurePath


def walkfiles(path: pathlib.Path) -> Iterator[pathlib.Path]:
    """Iterate over the files under the path."""
    if path.is_file():
        yield path
    elif path.is_dir():
        for entry in path.iterdir():
            yield from walkfiles(entry)
    else:  # pragma: no cover
        raise RuntimeError(f"{path}: not a regular file or directory")


def loadbuffers(root: pathlib.Path, *, relative_to: pathlib.Path) -> Iterator[Buffer]:
    """Iterate over the files in the filesystem."""
    # FIXME: bad name because the file is also read from disk the name
    # `loadfiles` is already used in domain.files for loading renderable files
    # (from files)

    for path in walkfiles(root):
        blob = path.read_text()
        mode = Mode.EXECUTABLE if os.access(path, os.X_OK) else Mode.DEFAULT
        path = path.relative_to(relative_to)
        yield Buffer(PurePath(*path.parts), mode, blob)


class FilesystemFileStorage(FileStorage):
    """Filesystem-based store for files."""

    def __init__(self, root: pathlib.Path) -> None:
        """Initialize."""
        self.root = root

    def store(self, file: File) -> None:
        """Commit a file to storage."""
        path = self.resolve(file.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file.read())
        if file.mode & Mode.EXECUTABLE:
            path.chmod(path.stat().st_mode | 0o111)

    def resolve(self, path: PurePath) -> pathlib.Path:
        """Resolve the path to a filesystem location."""
        return self.root.joinpath(*path.parts)

    @classmethod
    @contextmanager
    def temporary(cls) -> Iterator[FilesystemFileStorage]:
        """Return temporary storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir)
            yield cls(path)
