"""Unit tests for cutty.filestorage.adapters.disk."""
import contextlib
import os
import pathlib
import platform

import pytest

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.files import SymbolicLink
from cutty.filesystems.domain.purepath import PurePath


@pytest.fixture
def file() -> RegularFile:
    """Fixture for a regular file."""
    return RegularFile(
        PurePath("example", "README.md"),
        b"# example\n",
    )


@pytest.fixture
def executable() -> Executable:
    """Fixture for an executable file."""
    return Executable(
        PurePath("example", "main.py"),
        b"#!/usr/bin/env python",
    )


@pytest.fixture
def symlink() -> SymbolicLink:
    """Fixture for a symbolic link."""
    return SymbolicLink(
        PurePath("link"),
        PurePath("file"),
    )


@pytest.fixture
def storage(tmp_path: pathlib.Path) -> DiskFileStorage:
    """Fixture for a storage."""
    return DiskFileStorage(tmp_path)


def test_regular_file(file: RegularFile, storage: DiskFileStorage) -> None:
    """It stores the file."""
    with storage:
        storage.add(file)

    path = storage.resolve(file.path)
    assert path.read_bytes() == file.blob


class FakeError(Exception):
    """Exception used for testing rollback."""


def test_regular_file_undo(file: RegularFile, storage: DiskFileStorage) -> None:
    """It removes a created file when rolling back after an error."""
    with contextlib.suppress(FakeError):
        with storage:
            storage.add(file)
            raise FakeError()

    path = storage.resolve(file.path)
    assert not path.exists()


def test_directory_undo(file: RegularFile, storage: DiskFileStorage) -> None:
    """It removes a created directory when rolling back after an error."""
    with contextlib.suppress(FakeError):
        with storage:
            storage.add(file)
            raise FakeError()

    path = storage.resolve(file.path)
    assert not path.exists()
    assert not path.parent.exists()


def test_file_exists_raise(file: RegularFile, storage: DiskFileStorage) -> None:
    """It raises an exception if the file exists."""
    path = storage.resolve(file.path)
    path.parent.mkdir(parents=True)
    path.touch()

    with storage:
        with pytest.raises(FileExistsError):
            storage.add(file)


def test_file_exists_skip(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It skips existing files when requested."""
    storage = DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.SKIP)

    path = storage.resolve(file.path)
    path.parent.mkdir(parents=True)
    path.touch()

    with storage:
        storage.add(file)

    assert not path.read_bytes()


def test_file_exists_overwrite(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It overwrites an existing file when requested."""
    storage = DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE)

    path = storage.resolve(file.path)
    path.parent.mkdir(parents=True)
    path.touch()

    with storage:
        storage.add(file)

    assert path.read_bytes() == file.blob


def test_file_exists_overwrite_directory(
    tmp_path: pathlib.Path, file: RegularFile
) -> None:
    """It raises an exception if the target is an existing directory."""
    storage = DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE)

    path = storage.resolve(file.path)
    path.mkdir(parents=True)

    with storage:
        error = PermissionError if platform.system() == "Windows" else IsADirectoryError
        with pytest.raises(error):
            storage.add(file)


def test_file_exists_overwrite_undo(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It does not remove overwritten files when rolling back."""
    storage = DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE)

    path = storage.resolve(file.path)
    path.parent.mkdir(parents=True)
    path.touch()

    with contextlib.suppress(FakeError):
        with storage:
            storage.add(file)
            raise FakeError()

    assert path.exists()


def test_executable_blob(executable: Executable, storage: DiskFileStorage) -> None:
    """It stores the file."""
    with storage:
        storage.add(executable)

    path = storage.resolve(executable.path)
    assert path.read_bytes() == executable.blob


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Path.chmod ignores executable bits on Windows.",
)
def test_executable_mode(executable: File, storage: DiskFileStorage) -> None:
    """It stores the file."""
    with storage:
        storage.add(executable)

    path = storage.resolve(executable.path)
    assert os.access(path, os.X_OK)


def test_symlink(symlink: SymbolicLink, storage: DiskFileStorage) -> None:
    """It stores the file."""
    with storage:
        storage.add(symlink)

    path = storage.resolve(symlink.path)
    assert path.readlink().parts == symlink.target.parts


def test_symlink_overwrite_symlink(
    tmp_path: pathlib.Path, symlink: SymbolicLink
) -> None:
    """It raises an exception."""
    storage = DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE)

    path = storage.resolve(symlink.path)
    path.symlink_to(tmp_path)

    with storage:
        storage.add(symlink)

    assert path.readlink().parts == symlink.target.parts


def test_symlink_overwrite_file(tmp_path: pathlib.Path, symlink: SymbolicLink) -> None:
    """It raises an exception."""
    storage = DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE)

    path = storage.resolve(symlink.path)
    path.touch()

    with storage:
        with pytest.raises(FileExistsError):
            storage.add(symlink)


def test_unknown_filetype(storage: DiskFileStorage) -> None:
    """It raises a TypeError."""
    file = File(PurePath("dir", "file"))

    with pytest.raises(TypeError):
        with storage:
            storage.add(file)

    path = storage.resolve(file.path)
    assert not path.exists()
    assert not path.parent.exists()


def test_multiple_files(storage: DiskFileStorage, file: File, executable: File) -> None:
    """It stores all the files."""
    with storage:
        storage.add(executable)
        storage.add(file)

    assert all(storage.resolve(each.path).is_file() for each in (file, executable))


def test_already_exists(storage: DiskFileStorage, file: File) -> None:
    """It raises an exception if the file already exists."""
    with storage:
        storage.add(file)
        with pytest.raises(Exception):
            storage.add(file)


def test_overwrite_if_exists(tmp_path: pathlib.Path, file: File) -> None:
    """It overwrites existing files."""
    storage = DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE)

    path = storage.resolve(file.path)
    path.parent.mkdir()
    path.write_text("old")

    with storage:
        storage.add(file)

    assert path.read_text() != "old"


def test_skip_if_file_exists(tmp_path: pathlib.Path, file: File) -> None:
    """It skips existing files."""
    storage = DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.SKIP)

    path = storage.resolve(file.path)
    path.parent.mkdir()
    path.write_text("old")

    with storage:
        storage.add(file)

    assert path.read_text() == "old"
