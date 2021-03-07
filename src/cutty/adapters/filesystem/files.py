"""Filesystem implementation of the cutty.domain.files abstractions."""
import os
import pathlib
from collections.abc import Iterator

from cutty.domain.files import File
from cutty.domain.files import FileRepository
from cutty.domain.files import FileStorage
from cutty.domain.files import Mode
from cutty.domain.files import Path


def walkfiles(path: pathlib.Path) -> Iterator[pathlib.Path]:
    """Iterate over the files under the path."""
    if path.is_file():
        yield path
    elif path.is_dir():
        for entry in path.iterdir():
            yield from walkfiles(entry)
    else:  # pragma: no cover
        raise RuntimeError(f"{path}: not a regular file or directory")


class FilesystemFileRepository(FileRepository):
    """Filesystem-based repository of files."""

    def __init__(self, path: pathlib.Path, *, relative_to: pathlib.Path) -> None:
        """Initialize."""
        self.path = path
        self.root = relative_to

    def load(self) -> Iterator[File]:
        """Iterate over the files in the filesystem."""
        for path in walkfiles(self.path):
            blob = path.read_text()
            mode = Mode.EXECUTABLE if os.access(path, os.X_OK) else Mode.DEFAULT
            path = path.relative_to(self.root)
            yield File(Path(path.parts), mode, blob)


class FilesystemFileStorage(FileStorage):
    """Filesystem-based store for files."""

    def __init__(self, root: pathlib.Path) -> None:
        """Initialize."""
        self.root = root

    def store(self, file: File) -> None:
        """Commit a file to storage."""
        path = self.root.joinpath(*file.path.parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file.blob)
        if file.mode & Mode.EXECUTABLE:
            path.chmod(path.stat().st_mode | 0o111)
