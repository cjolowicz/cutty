"""Unit tests for cutty.filesystems.adapters.dict."""
from typing import Any

import pytest

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath


def test_lookup_curdir() -> None:
    """It returns the current directory."""
    filesystem = DictFilesystem({"file": ""})
    path = PurePath(".")
    [entry] = filesystem.iterdir(path)
    assert entry == "file"


def test_lookup_pardir_normal() -> None:
    """It returns the parent directory."""
    filesystem = DictFilesystem({"dir": {}})
    path = PurePath("dir", "..")
    [entry] = filesystem.iterdir(path)
    assert entry == "dir"


def test_lookup_pardir_root() -> None:
    """It returns the root directory."""
    filesystem = DictFilesystem({"file": ""})
    path = PurePath("..")
    [entry] = filesystem.iterdir(path)
    assert entry == "file"


def test_is_dir_notfound() -> None:
    """It returns False."""
    filesystem = DictFilesystem({})
    path = PurePath("dir")
    assert not filesystem.is_dir(path)


def test_is_file_notfound() -> None:
    """It returns False."""
    filesystem = DictFilesystem({})
    path = PurePath("file")
    assert not filesystem.is_file(path)


def test_is_symlink_notfound() -> None:
    """It returns False."""
    filesystem = DictFilesystem({})
    path = PurePath("file")
    assert not filesystem.is_symlink(path)


def test_access_notfound() -> None:
    """It returns False."""
    filesystem = DictFilesystem({})
    path = PurePath("file")
    assert not filesystem.access(path, Access.DEFAULT)


def test_access_exists() -> None:
    """It returns True."""
    filesystem = DictFilesystem({})
    path = PurePath()
    assert filesystem.access(path, Access.DEFAULT)


@pytest.mark.parametrize(
    "path",
    [
        PurePath("file", "."),
        PurePath("file", ".."),
        PurePath("file", "file"),
    ],
    ids=str,
)
def test_read_text_not_a_directory(path: PurePath) -> None:
    """It raises an exception."""
    filesystem = DictFilesystem({"file": ""})
    with pytest.raises(NotADirectoryError):
        filesystem.read_text(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath("dir"),
        PurePath("."),
        PurePath(".."),
        PurePath("link"),
    ],
    ids=str,
)
def test_read_text_is_a_directory(path: PurePath) -> None:
    """It raises an exception."""
    filesystem = DictFilesystem({"dir": {}, "link": PurePath("dir")})
    with pytest.raises(IsADirectoryError):
        filesystem.read_text(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath("link", "."),
        PurePath("link", ".."),
        PurePath("link", "file"),
    ],
    ids=str,
)
def test_readlink_not_a_directory(path: PurePath) -> None:
    """It raises an exception."""
    filesystem = DictFilesystem({"file": "", "link": PurePath("file")})
    with pytest.raises(NotADirectoryError):
        filesystem.readlink(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath(),
        PurePath("."),
        PurePath(".."),
        PurePath("dir"),
        PurePath("file"),
    ],
    ids=str,
)
def test_readlink_not_a_symlink(path: PurePath) -> None:
    """It raises an exception."""
    filesystem = DictFilesystem({"file": "", "dir": {}})
    with pytest.raises(Exception):
        filesystem.readlink(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath("file"),
        PurePath("link"),
    ],
    ids=str,
)
def test_iterdir_not_a_directory(path: PurePath) -> None:
    """It raises an exception."""
    filesystem = DictFilesystem({"file": "", "link": PurePath("file")})
    with pytest.raises(NotADirectoryError):
        next(filesystem.iterdir(path))


@pytest.fixture
def dictionary() -> dict[str, Any]:
    """Fixture for the dictionary backing a filesystem."""
    return {
        "etc": {"passwd": "root:x:0:0:root:/root:/bin/sh"},
        "root": {".profile": "# .profile\n"},
        "home": {"root": PurePath("..", "root")},
    }


@pytest.fixture
def filesystem(dictionary: dict[str, Any]) -> DictFilesystem:
    """Fixture for a filesystem."""
    return DictFilesystem(dictionary)


@pytest.fixture
def root(filesystem: Filesystem) -> Path:
    """Fixture for a filesystem root."""
    return Path(filesystem=filesystem)


def test_hash(
    root: Path, filesystem: DictFilesystem, dictionary: dict[str, Any]
) -> None:
    """It returns a hash value."""
    a1 = root / "a"
    a2 = Path(filesystem=DictFilesystem(dictionary)) / "a"
    assert hash(a1) != hash(a2)


def test_cmp_self(root: Path) -> None:
    """It compares the paths."""
    a = root / "a"
    assert a == a
    assert not (a < a)
    assert not (a > a)
    assert a <= a
    assert a >= a


def test_cmp_other(root: Path) -> None:
    """It compares the parts."""
    a, b = [root / name for name in "ab"]
    assert a != b
    assert a < b
    assert a <= b
    assert not (a > b)
    assert not (a >= b)


def test_cmp_other_type(root: Path) -> None:
    """It compares the paths."""
    a1 = root / "a"
    a2 = "teapot"

    assert a1 != a2

    with pytest.raises(TypeError):
        a1 < a2  # noqa: B015

    with pytest.raises(TypeError):
        a1 > a2  # noqa: B015

    with pytest.raises(TypeError):
        a1 <= a2  # noqa: B015

    with pytest.raises(TypeError):
        a1 >= a2  # noqa: B015


def test_cmp_other_filesystem(
    root: Path, filesystem: DictFilesystem, dictionary: dict[str, Any]
) -> None:
    """It compares the paths."""
    a1 = root / "a"
    a2 = Path(filesystem=DictFilesystem(dictionary)) / "a"

    assert a1 != a2
    assert a1 != "teapot"

    with pytest.raises(ValueError):
        a1 < a2  # noqa: B015

    with pytest.raises(ValueError):
        a1 > a2  # noqa: B015

    with pytest.raises(ValueError):
        a1 <= a2  # noqa: B015

    with pytest.raises(ValueError):
        a1 >= a2  # noqa: B015


def test_parent_root(root: Path) -> None:
    """It returns the root."""
    assert root.parent == root


def test_parent_file(root: Path) -> None:
    """It returns the parent directory."""
    path = root / "etc" / "passwd"
    assert path.parent == root / "etc"


def test_iterdir_root(root: Path) -> None:
    """It iterates over the files in the directory."""
    first, second, third = root.iterdir()
    assert str(first) == "etc"
    assert str(second) == "root"
    assert str(third) == "home"


def test_iterdir_directory(root: Path) -> None:
    """It iterates over the files in the directory."""
    path = root / "etc"
    [path] = path.iterdir()
    assert str(path) == "etc/passwd"


def test_read_text(root: Path) -> None:
    """It returns the file contents."""
    path = root / "root" / ".profile"
    assert path.read_text() == "# .profile\n"


def test_read_text_symlink(root: Path) -> None:
    """It returns the file contents."""
    path = root / "home" / "root" / ".profile"
    assert path.read_text() == "# .profile\n"


def test_is_file(root: Path) -> None:
    """It returns False if the path is not a regular file."""
    path = root / "etc"
    assert not path.is_file()


def test_is_dir(root: Path) -> None:
    """It returns False if the path is a not directory."""
    path = root / "root" / ".profile"
    assert not path.is_dir()


def test_is_symlink_false(root: Path) -> None:
    """It returns False if the path is not a symbolic link."""
    path = root / "etc"
    assert not path.is_symlink()


def test_is_symlink_true(root: Path) -> None:
    """It returns True if the path is a symbolic link."""
    path = root / "home" / "root"
    assert path.is_symlink()


def test_readlink_good(root: Path) -> None:
    """It returns the target path."""
    path = root / "home" / "root"
    assert path.readlink() == PurePath() / ".." / "root"


def test_readlink_bad(root: Path) -> None:
    """It raises if the path is not a symbolic link."""
    path = root / "etc"
    with pytest.raises(IsADirectoryError):
        path.readlink()


def test_access(root: Path) -> None:
    """It returns False if the path cannot be accessed as specified."""
    path = root / "etc" / "passwd"
    assert not path.access(Access.EXECUTE)
