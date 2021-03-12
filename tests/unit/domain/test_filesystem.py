"""Unit tests for cutty.domain.filesystem."""
from collections.abc import Iterator
from typing import Any

import pytest

from cutty.domain.filesystem import Access
from cutty.domain.filesystem import Filesystem
from cutty.domain.filesystem import Path


@pytest.mark.parametrize(
    "parts",
    [
        [],
        ["README.md"],
        ["example", "README.md"],
        [""],
        ["example", ""],
        ["", "example"],
        ["example", "", "README.md"],
        ["/", "boot", "vmlinuz"],
        ["\\", "system32", "hal.dll"],
        ["..", "README.md"],
        ["example", ".", "README.md"],
    ],
)
def test_valid(parts: list[str]) -> None:
    """It returns a Path instance."""
    assert Path(*parts)


def test_div() -> None:
    """It returns a path with the part appended."""
    assert Path("etc") / "passwd" == Path("etc", "passwd")


@pytest.mark.parametrize(
    "path,expected",
    [
        (Path(), ""),
        (Path("README.md"), "README.md"),
        (Path("example", "README.md"), "README.md"),
    ],
)
def test_name(path: Path, expected: str) -> None:
    """It returns the final component, if any."""
    assert path.name == expected


@pytest.mark.parametrize(
    "path,expected",
    [
        (Path(), ""),
        (Path("README"), "README"),
        (Path("README.md"), "README"),
        (Path("example", "README.md"), "README"),
        (Path("archive.tar.gz"), "archive.tar"),
        (Path(".profile"), ".profile"),
    ],
)
def test_stem(path: Path, expected: str) -> None:
    """It returns the final component, minus its last suffix."""
    assert path.stem == expected


class DictFilesystem(Filesystem):
    """Dictionary-based filesystem for your pocket."""

    def __init__(self, tree: Any) -> None:
        """Initialize."""
        # Tree = str | Path | dict[str, Tree]
        self.tree = tree

    def _lookup(self, path: Path) -> Any:
        def _resolve(entry: Any, current: Path) -> tuple[Any, Path]:
            if isinstance(entry, Path):
                current = current.parent.joinpath(*entry.parts)
                entry = self._lookup(current)
            return entry, current

        entry, current = _resolve(self.tree, Path())
        for part in path.parts:
            current /= part
            entry, current = _resolve(entry[part], current)
        return entry

    def iterdir(self, path: Path) -> Iterator[Path]:
        """Iterate over the files in this directory."""
        entry = self._lookup(path)
        assert isinstance(entry, dict)
        for key in self._lookup(path):
            yield path / key

    def read_text(self, path: Path) -> str:
        """Return the contents of this file."""
        entry = self._lookup(path)
        assert isinstance(entry, str)
        return entry

    def is_file(self, path: Path) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        try:
            entry = self._lookup(path)
        except KeyError:
            return False
        return isinstance(entry, str)

    def is_dir(self, path: Path) -> bool:
        """Return True if this is a directory."""
        try:
            entry = self._lookup(path)
        except KeyError:
            return False
        return isinstance(entry, dict)

    def is_symlink(self, path: Path) -> bool:
        """Return True if this is a symbolic link."""
        try:
            entry = self._lookup(path.parent)[path.name]
        except KeyError:
            return False
        return isinstance(entry, Path)

    def readlink(self, path: Path) -> Path:
        """Return the target of a symbolic link."""
        entry = self._lookup(path.parent)[path.name]
        if not isinstance(entry, Path):
            raise ValueError("not a symbolic link")
        return entry

    def access(self, path: Path, mode: Access) -> bool:
        """Return True if the user can access the path."""
        try:
            self._lookup(path)
        except KeyError:
            return False
        if mode & Access.EXECUTE:
            return self.is_dir(path)
        return True


@pytest.fixture
def filesystem() -> Filesystem:
    """Fixture for a filesystem."""
    return DictFilesystem(
        {
            "etc": {"passwd": "root:x:0:0:root:/root:/bin/sh"},
            "root": {".profile": "# .profile\n"},
            "root2": Path("root"),
        }
    )


def test_hash(filesystem: DictFilesystem) -> None:
    """It returns a hash value."""
    a1 = filesystem.root / "a"
    a2 = DictFilesystem(filesystem.tree).root / "a"
    assert hash(a1) != hash(a2)


def test_cmp_self(filesystem: Filesystem) -> None:
    """It compares the paths."""
    a = filesystem.root / "a"
    assert a == a
    assert not (a < a)
    assert not (a > a)
    assert a <= a
    assert a >= a


def test_cmp_other(filesystem: Filesystem) -> None:
    """It compares the parts."""
    a, b = [filesystem.root / name for name in "ab"]
    assert a != b
    assert a < b
    assert a <= b
    assert not (a > b)
    assert not (a >= b)


def test_cmp_other_type(filesystem: DictFilesystem) -> None:
    """It compares the paths."""
    a1 = filesystem.root / "a"
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


def test_cmp_other_filesystem(filesystem: DictFilesystem) -> None:
    """It compares the paths."""
    a1 = filesystem.root / "a"
    a2 = DictFilesystem(filesystem.tree).root / "a"

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


def test_parent_root(filesystem: Filesystem) -> None:
    """It returns the root."""
    assert filesystem.root.parent == filesystem.root


def test_parent_file(filesystem: Filesystem) -> None:
    """It returns the parent directory."""
    path = filesystem.root / "etc" / "passwd"
    assert path.parent == filesystem.root / "etc"


def test_iterdir_root(filesystem: Filesystem) -> None:
    """It iterates over the files in the directory."""
    first, second, third = filesystem.root.iterdir()
    assert str(first) == "etc"
    assert str(second) == "root"
    assert str(third) == "root2"


def test_iterdir_directory(filesystem: Filesystem) -> None:
    """It iterates over the files in the directory."""
    path = filesystem.root / "etc"
    [path] = path.iterdir()
    assert str(path) == "etc/passwd"


def test_read_text(filesystem: Filesystem) -> None:
    """It returns the file contents."""
    path = filesystem.root / "root2" / ".profile"
    assert path.read_text() == "# .profile\n"


def test_is_file(filesystem: Filesystem) -> None:
    """It returns False if the path is not a regular file."""
    path = filesystem.root / "etc"
    assert not path.is_file()


def test_is_dir(filesystem: Filesystem) -> None:
    """It returns False if the path is a not directory."""
    path = filesystem.root / "root" / ".profile"
    assert not path.is_dir()


def test_is_symlink_false(filesystem: Filesystem) -> None:
    """It returns False if the path is not a symbolic link."""
    path = filesystem.root / "etc"
    assert not path.is_symlink()


def test_is_symlink_true(filesystem: Filesystem) -> None:
    """It returns True if the path is a symbolic link."""
    path = filesystem.root / "root2"
    assert path.is_symlink()


def test_readlink_good(filesystem: Filesystem) -> None:
    """It returns the target path."""
    path = filesystem.root / "root2"
    assert path.readlink() == filesystem.root / "root"


def test_readlink_bad(filesystem: Filesystem) -> None:
    """It raises if the path is not a symbolic link."""
    path = filesystem.root / "etc"
    with pytest.raises(ValueError):
        path.readlink()


def test_access(filesystem: Filesystem) -> None:
    """It returns False if the path cannot be accessed as specified."""
    path = filesystem.root / "etc" / "passwd"
    assert not path.access(Access.EXECUTE)
