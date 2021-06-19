"""Simple in-memory file storage."""
from collections.abc import Iterator
from collections.abc import MutableSequence

from cutty.compat.contextlib import contextmanager
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.storage import FileStorage
from cutty.filestorage.domain.storage import FileStore


@contextmanager
def memoryfilestorage(files: MutableSequence[File]) -> Iterator[FileStore]:
    """Append files to a mutable sequence."""
    with MemoryFileStorage(files) as storage:
        yield storage.add


class MemoryFileStorage(FileStorage):
    """In-memory file storage for testing."""

    def __init__(self, files: MutableSequence[File]) -> None:
        """Initialize."""
        self.files = files

    def add(self, file: File) -> None:
        """Add the file to the storage."""
        self.files.append(file)

    def rollback(self) -> None:
        """Rollback all stores."""
        self.files.clear()
