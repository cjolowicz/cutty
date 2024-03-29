"""Unit tests for cutty.filestorage.domain.files."""
import pytest

from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import loadfile
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.files import SymbolicLink
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath


@pytest.fixture
def filesystem() -> Filesystem:
    """Fixture with a filesystem for testing."""
    tree = {"file": "Lorem ipsum dolor", "link": PurePath("file")}
    return DictFilesystem(tree)


def test_load_regularfile(filesystem: Filesystem) -> None:
    """It loads a regular file."""
    path = Path("file", filesystem=filesystem)
    file = loadfile(path)
    assert isinstance(file, RegularFile)
    assert file.path == path
    assert file.blob == path.read_bytes()


def test_load_symlink_follow(filesystem: Filesystem) -> None:
    """It follows a symbolic link."""
    path = Path("link", filesystem=filesystem)
    file = loadfile(path)
    assert isinstance(file, RegularFile)
    assert file.path == path
    assert file.blob == path.read_bytes()


def test_load_symlink_nofollow(filesystem: Filesystem) -> None:
    """It loads a symbolic link."""
    path = Path("link", filesystem=filesystem)
    file = loadfile(path, follow_symlinks=False)
    assert isinstance(file, SymbolicLink)
    assert file.path == path
    assert file.target == PurePath("file")


def test_load_directory(filesystem: Filesystem) -> None:
    """It raises an exception when passed a directory."""
    path = Path(filesystem=filesystem)
    with pytest.raises(Exception):
        loadfile(path, follow_symlinks=False)


def test_withpath_regularfile(filesystem: Filesystem) -> None:
    """It replaces the path of a regular file."""
    path1 = PurePath("dir", "file")
    path2 = PurePath("file")

    file1 = RegularFile(path1, b"Lorem ipsum dolor")
    file2 = file1.withpath(path2)

    assert isinstance(file2, RegularFile)
    assert file2.path == path2
    assert file2.blob == file1.blob


def test_withpath_executable(filesystem: Filesystem) -> None:
    """It replaces the path of an executable file."""
    path1 = PurePath("dir", "exec")
    path2 = PurePath("exec")

    exec1 = Executable(path1, b":")
    exec2 = exec1.withpath(path2)

    assert isinstance(exec2, Executable)
    assert exec2.path == path2
    assert exec2.blob == exec1.blob


def test_withpath_symlink(filesystem: Filesystem) -> None:
    """It replaces the path of a symbolic link."""
    path1 = PurePath("dir", "link")
    path2 = PurePath("link")

    link1 = SymbolicLink(path1, PurePath("file"))
    link2 = link1.withpath(path2)

    assert isinstance(link2, SymbolicLink)
    assert link2.path == path2
    assert link2.target == link1.target
