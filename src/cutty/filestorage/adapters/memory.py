"""Simple in-memory file storage."""
from collections.abc import Iterator
from collections.abc import MutableSequence

from cutty.compat.contextlib import contextmanager
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.storage import FileStore


@contextmanager
def memoryfilestorage(files: MutableSequence[File]) -> Iterator[FileStore]:
    """Append files to a mutable sequence."""
    yield files.append
