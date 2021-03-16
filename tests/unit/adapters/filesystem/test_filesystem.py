"""Unit tests for cutty.adapters.filesystem.filesystem."""
import pathlib

import pytest

from cutty.adapters.filesystem.filesystem import DiskFilesystem


@pytest.fixture
def filesystem(tmp_path: pathlib.Path) -> DiskFilesystem:
    """Return a disk filesystem."""
    return DiskFilesystem(tmp_path)


def test_is_dir(filesystem: DiskFilesystem) -> None:
    """It returns True if the path is a directory."""
    assert filesystem.root.is_dir()


def test_iterdir(filesystem: DiskFilesystem) -> None:
    """It iterates over the files."""
    (filesystem.resolve(filesystem.root) / "filename").touch()

    [path] = filesystem.root.iterdir()
    [part] = path.parts

    assert part == "filename"


def test_is_file(filesystem: DiskFilesystem) -> None:
    """It returns True if the path is a file."""
    (filesystem.resolve(filesystem.root) / "filename").touch()
    assert (filesystem.root / "filename").is_file()


def test_read_text(filesystem: DiskFilesystem) -> None:
    """It returns the file contents."""
    (filesystem.resolve(filesystem.root) / "filename").write_text("Lorem")
    assert (filesystem.root / "filename").read_text() == "Lorem"


def test_is_symlink(filesystem: DiskFilesystem) -> None:
    """It returns True if the path is a symlink."""
    (filesystem.resolve(filesystem.root) / "filename").symlink_to("target")
    assert (filesystem.root / "filename").is_symlink()


def test_readlink(filesystem: DiskFilesystem) -> None:
    """It returns the link target."""
    (filesystem.resolve(filesystem.root) / "filename").symlink_to("target")
    [target] = (filesystem.root / "filename").readlink().parts
    assert target == "target"


def test_access(filesystem: DiskFilesystem) -> None:
    """It returns True if the file can be accessed."""
    (filesystem.resolve(filesystem.root) / "filename").touch()
    assert (filesystem.root / "filename").access()


def test_eq(filesystem: DiskFilesystem) -> None:
    """It returns True if the paths are the same."""
    assert filesystem.root == filesystem.root


def test_lt(filesystem: DiskFilesystem) -> None:
    """It returns False if the paths are the same."""
    assert filesystem.root <= filesystem.root
