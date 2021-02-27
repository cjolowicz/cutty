"""Filesystem implementation of the cutty.domain.files abstractions."""
import pathlib

from cutty.domain.files import File
from cutty.domain.files import FileStorage


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
