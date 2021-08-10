"""Unit tests for cutty.filesystems.domain.pathfs."""
from typing import Any

import pytest

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.pathfs import PathFilesystem
from cutty.filesystems.domain.purepath import PurePath


def root(tree: dict[str, Any], *, innerpath: PurePath) -> Path:
    """Return the root of a path filesystem constructed from the tree."""
    basefilesystem = DictFilesystem(tree)
    path = Path(filesystem=basefilesystem).joinpath(*innerpath.parts)
    return Path(filesystem=PathFilesystem(path))


@pytest.fixture
def path() -> Path:
    """Fixture for the root of a path filesystem."""
    return root(
        {"dir": {"file": "text", "link": PurePath("file")}},
        innerpath=PurePath("dir"),
    )


def test_is_dir(path: Path) -> None:
    """It returns True if the path is a directory."""
    assert path.is_dir()


def test_is_file(path: Path) -> None:
    """It returns True if the path is a file."""
    assert (path / "file").is_file()


def test_is_symlink(path: Path) -> None:
    """It returns True if the path is a symbolic link."""
    assert (path / "link").is_symlink()


def test_read_bytes(path: Path) -> None:
    """It returns the contents of the file located at the path."""
    assert b"text" == (path / "file").read_bytes()


def test_read_text(path: Path) -> None:
    """It returns the contents of the file located at the path."""
    assert "text" == (path / "file").read_text()


def test_readlink(path: Path) -> None:
    """It returns the target of the symbolic link."""
    assert PurePath("file") == (path / "link").readlink()


def test_iterdir(path: Path) -> None:
    """It yields the directory entries."""
    [file, link] = path.iterdir()
    assert file.name == "file"
    assert link.name == "link"


def test_access(path: Path) -> None:
    """It returns True if the path exists."""
    assert path.access()


def test_constrain_symlinks_to_filesystem() -> None:
    """It does not allow symbolic links to break out of the filesystem."""
    path = root(
        {
            "file": "text",
            "dir": {"link": PurePath("..", "file")},
        },
        innerpath=PurePath("dir"),
    )
    # XXX Should we rewrite the error message to hide the 'dir/' prefix?
    with pytest.raises(FileNotFoundError, match="file not found: dir/file"):
        assert (path / "link").read_text()
