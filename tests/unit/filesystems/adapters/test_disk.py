"""Unit tests for cutty.filesystems.adapters.disk."""
import pathlib

import pytest

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.path import Path


@pytest.fixture
def filesystem(tmp_path: pathlib.Path) -> DiskFilesystem:
    """Return a disk filesystem."""
    path = tmp_path / "diskfilesystem"
    path.mkdir()
    return DiskFilesystem(path)


@pytest.fixture
def root(filesystem: Filesystem) -> Path:
    """Fixture for a filesystem root."""
    return Path(filesystem=filesystem)


def test_is_dir(root: Path) -> None:
    """It returns True if the path is a directory."""
    assert root.is_dir()


def test_iterdir(root: Path, filesystem: DiskFilesystem) -> None:
    """It iterates over the files."""
    (filesystem.resolve(root) / "filename").touch()

    [path] = root.iterdir()
    [part] = path.parts

    assert part == "filename"


def test_is_file(root: Path, filesystem: DiskFilesystem) -> None:
    """It returns True if the path is a file."""
    (filesystem.resolve(root) / "filename").touch()
    assert (root / "filename").is_file()


def test_read_text(root: Path, filesystem: DiskFilesystem) -> None:
    """It returns the file contents."""
    (filesystem.resolve(root) / "filename").write_text("Lorem")
    assert (root / "filename").read_text() == "Lorem"


def test_is_symlink(root: Path, filesystem: DiskFilesystem) -> None:
    """It returns True if the path is a symlink."""
    (filesystem.resolve(root) / "filename").symlink_to("target")
    assert (root / "filename").is_symlink()


def test_readlink(root: Path, filesystem: DiskFilesystem) -> None:
    """It returns the link target."""
    (filesystem.resolve(root) / "filename").symlink_to("target")
    [target] = (root / "filename").readlink().parts
    assert target == "target"


def test_access(root: Path, filesystem: DiskFilesystem) -> None:
    """It returns True if the file can be accessed."""
    (filesystem.resolve(root) / "filename").touch()
    assert (root / "filename").access()


def test_eq(root: Path) -> None:
    """It returns True if the paths are the same."""
    assert root == root


def test_lt(root: Path) -> None:
    """It returns False if the paths are the same."""
    assert root <= root
