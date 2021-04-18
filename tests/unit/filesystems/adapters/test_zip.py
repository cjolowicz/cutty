"""Unit tests for cutty.filesystems.adapters.zip."""
import platform
import shutil
from pathlib import Path

import pytest

from cutty.filesystems.adapters.zip import ZipFilesystem
from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.purepath import PurePath


@pytest.fixture
def filesystem(tmp_path: Path) -> ZipFilesystem:
    """Fixture for a zip filesystem."""
    path = tmp_path / "archive"
    path.mkdir()

    (path / "file").write_text("lorem ipsum dolor\n")
    (path / "dir").mkdir()
    (path / "dir" / "script.py").write_text("#!/usr/bin/env python\n")
    (path / "dir" / "script.py").chmod(0o755)
    (path / "dir" / "subdir").mkdir()
    (path / "dir" / "subdir" / ".keep").touch()

    shutil.make_archive(str(path), "zip", str(path))

    return ZipFilesystem(path.with_suffix(".zip"))


@pytest.mark.parametrize(
    "path",
    [
        PurePath(),
        PurePath("dir"),
        PurePath("dir", "subdir"),
        PurePath("."),
        PurePath(".."),
        PurePath("..", ".."),
        PurePath("dir", "."),
        PurePath("dir", ".."),
        PurePath(".", "dir"),
        PurePath("..", "dir"),
        PurePath("dir", ".", "subdir"),
        PurePath("dir", "subdir", ".."),
    ],
    ids=str,
)
def test_is_dir_true(filesystem: ZipFilesystem, path: PurePath) -> None:
    """It returns True."""
    assert filesystem.is_dir(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath("file"),
        PurePath("dir", "script.py"),
        PurePath("dir", "subdir", ".keep"),
    ],
    ids=str,
)
def test_is_dir_false(filesystem: ZipFilesystem, path: PurePath) -> None:
    """It returns False."""
    assert not filesystem.is_dir(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath("file"),
        PurePath("dir", "script.py"),
        PurePath("dir", "subdir", ".keep"),
        PurePath(".", "file"),
        PurePath("dir", "..", "file"),
        PurePath("dir", "script.py"),
        PurePath("dir", "subdir", ".keep"),
    ],
    ids=str,
)
def test_is_file_true(filesystem: ZipFilesystem, path: PurePath) -> None:
    """It returns True."""
    assert filesystem.is_file(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath(),
        PurePath("dir"),
        PurePath("dir", "subdir"),
        PurePath("."),
        PurePath(".."),
        PurePath("..", ".."),
        PurePath("dir", "."),
        PurePath("dir", ".."),
        PurePath(".", "dir"),
        PurePath("..", "dir"),
        PurePath("dir", ".", "subdir"),
        PurePath("dir", "subdir", ".."),
        PurePath("no such file"),
        PurePath("dir", "no such file"),
    ],
    ids=str,
)
def test_is_file_false(filesystem: ZipFilesystem, path: PurePath) -> None:
    """It returns False."""
    assert not filesystem.is_file(path)


def test_read_bytes(filesystem: ZipFilesystem) -> None:
    """It returns the file contents."""
    assert filesystem.read_bytes(PurePath("file")) == b"lorem ipsum dolor\n"


def test_read_text(filesystem: ZipFilesystem) -> None:
    """It returns the file contents."""
    assert filesystem.read_text(PurePath("file")) == "lorem ipsum dolor\n"


def test_readlink(filesystem: ZipFilesystem) -> None:
    """It raises an exception."""
    with pytest.raises(Exception):
        filesystem.readlink(PurePath("file"))


@pytest.mark.parametrize(
    "path,entries",
    [
        (PurePath(), {"dir", "file"}),
        (PurePath("."), {"dir", "file"}),
        (PurePath(".."), {"dir", "file"}),
        (PurePath("dir", ".."), {"dir", "file"}),
        (PurePath("dir"), {"subdir", "script.py"}),
        (PurePath("dir", "subdir"), {".keep"}),
    ],
    ids=str,
)
def test_iterdir(filesystem: ZipFilesystem, path: PurePath, entries: set[str]) -> None:
    """It iterates over the directory entries."""
    assert set(filesystem.iterdir(path)) == entries


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Windows has no executable filemode"
)
def test_access_executable(filesystem: ZipFilesystem) -> None:
    """It returns True if the file can be executed."""
    assert filesystem.access(PurePath("dir", "script.py"), Access.EXECUTE)


def test_access_read(filesystem: ZipFilesystem) -> None:
    """It returns True if the file can be read."""
    assert filesystem.access(PurePath("file"), Access.READ)


def test_access_exists(filesystem: ZipFilesystem) -> None:
    """It returns True if the file exists."""
    assert filesystem.access(PurePath("file"), Access.DEFAULT)


def test_access_not_exists(filesystem: ZipFilesystem) -> None:
    """It returns False if the file does not exist."""
    assert not filesystem.access(PurePath("bogus"), Access.DEFAULT)
