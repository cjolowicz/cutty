"""Unit tests for cutty.filestorage.adapters.memory."""
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
