"""Unit tests for cutty.filestorage.adapters.memory."""
import pytest

from cutty.filestorage.adapters.memory import memoryfilestorage
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.domain.purepath import PurePath


def test_store() -> None:
    """It stores the file."""
    file = RegularFile(PurePath("file"), b"Lorem")
    files: list[File] = []
    with memoryfilestorage(files) as storefile:
        storefile(file)
    assert file in files


def test_rollback() -> None:
    """It clears the list."""
    # FIXME: don't let callers expect their original list is preserved
    file = RegularFile(PurePath("file"), b"Lorem")
    files: list[File] = []
    with pytest.raises(RuntimeError):
        with memoryfilestorage(files) as storefile:
            storefile(file)
            raise RuntimeError()
    assert not files
