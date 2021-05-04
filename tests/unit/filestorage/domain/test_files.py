"""Unit tests for cutty.filestorage.domain.files."""
import pytest

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
