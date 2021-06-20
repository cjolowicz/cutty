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
from cutty.filestorage.domain.storage import FileStorage
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
def storage(tmp_path: pathlib.Path) -> FileStorage:
    """Fixture for a storage."""
    return DiskFileStorage(tmp_path)


def test_regular_file(
    tmp_path: pathlib.Path, file: RegularFile, storage: FileStorage
) -> None:
    """It stores the file."""
    with storage:
        storage.add(file)

    path = tmp_path.joinpath(*file.path.parts)
    assert path.read_bytes() == file.blob


class FakeError(Exception):
    """Exception used for testing rollback."""


def test_regular_file_undo(
    tmp_path: pathlib.Path, file: RegularFile, storage: FileStorage
) -> None:
    """It removes a created file when rolling back after an error."""
    with contextlib.suppress(FakeError):
        with storage:
            storage.add(file)
            raise FakeError()

    path = tmp_path.joinpath(*file.path.parts)
    assert not path.exists()


def test_directory_undo(
    tmp_path: pathlib.Path, file: RegularFile, storage: FileStorage
) -> None:
    """It removes a created directory when rolling back after an error."""
    with contextlib.suppress(FakeError):
        with storage:
            storage.add(file)
            raise FakeError()

    path = tmp_path.joinpath(*file.path.parts)
    assert not path.exists()
    assert not path.parent.exists()


def test_file_exists_raise(
    tmp_path: pathlib.Path, file: RegularFile, storage: FileStorage
) -> None:
    """It raises an exception if the file exists."""
    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir(parents=True)
    path.touch()

    with storage:
        with pytest.raises(FileExistsError):
            storage.add(file)


def test_file_exists_skip(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It skips existing files when requested."""
    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir(parents=True)
    path.touch()

    with DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.SKIP) as storage:
        storage.add(file)

    assert not path.read_bytes()


def test_file_exists_overwrite(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It overwrites an existing file when requested."""
    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir(parents=True)
    path.touch()

    with DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storage:
        storage.add(file)

    assert path.read_bytes() == file.blob


def test_file_exists_overwrite_directory(
    tmp_path: pathlib.Path, file: RegularFile
) -> None:
    """It raises an exception if the target is an existing directory."""
    path = tmp_path.joinpath(*file.path.parts)
    path.mkdir(parents=True)

    with DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storage:
        error = PermissionError if platform.system() == "Windows" else IsADirectoryError
        with pytest.raises(error):
            storage.add(file)


def test_file_exists_overwrite_undo(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It does not remove overwritten files when rolling back."""
    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir(parents=True)
    path.touch()

    with contextlib.suppress(FakeError):
        with DiskFileStorage(
            tmp_path, fileexists=FileExistsPolicy.OVERWRITE
        ) as storage:
            storage.add(file)
            raise FakeError()

    assert path.exists()


def test_executable_blob(
    tmp_path: pathlib.Path, executable: Executable, storage: FileStorage
) -> None:
    """It stores the file."""
    with storage:
        storage.add(executable)

    path = tmp_path.joinpath(*executable.path.parts)
    assert path.read_bytes() == executable.blob


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Path.chmod ignores executable bits on Windows.",
)
def test_executable_mode(
    tmp_path: pathlib.Path, executable: File, storage: FileStorage
) -> None:
    """It stores the file."""
    with storage:
        storage.add(executable)

    path = tmp_path.joinpath(*executable.path.parts)
    assert os.access(path, os.X_OK)


def test_symlink(
    tmp_path: pathlib.Path, symlink: SymbolicLink, storage: FileStorage
) -> None:
    """It stores the file."""
    with storage:
        storage.add(symlink)

    path = tmp_path.joinpath(*symlink.path.parts)
    assert path.readlink().parts == symlink.target.parts


def test_symlink_overwrite_symlink(
    tmp_path: pathlib.Path, symlink: SymbolicLink
) -> None:
    """It raises an exception."""
    path = tmp_path.joinpath(*symlink.path.parts)
    path.symlink_to(tmp_path)

    with DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storage:
        storage.add(symlink)

    assert path.readlink().parts == symlink.target.parts


def test_symlink_overwrite_file(tmp_path: pathlib.Path, symlink: SymbolicLink) -> None:
    """It raises an exception."""
    path = tmp_path.joinpath(*symlink.path.parts)
    path.touch()

    with DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storage:
        with pytest.raises(FileExistsError):
            storage.add(symlink)


def test_unknown_filetype(tmp_path: pathlib.Path, storage: FileStorage) -> None:
    """It raises a TypeError."""
    file = File(PurePath("dir", "file"))

    with pytest.raises(TypeError):
        with storage:
            storage.add(file)

    path = tmp_path.joinpath(*file.path.parts)
    assert not path.exists()
    assert not path.parent.exists()


def test_multiple_files(
    tmp_path: pathlib.Path, storage: FileStorage, file: File, executable: File
) -> None:
    """It stores all the files."""
    with storage:
        storage.add(executable)
        storage.add(file)

    assert all(
        tmp_path.joinpath(*each.path.parts).is_file() for each in (file, executable)
    )


def test_already_exists(storage: FileStorage, file: File) -> None:
    """It raises an exception if the file already exists."""
    with storage:
        storage.add(file)
        with pytest.raises(Exception):
            storage.add(file)


def test_overwrite_if_exists(tmp_path: pathlib.Path, file: File) -> None:
    """It overwrites existing files."""
    storage = DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE)

    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir()
    path.write_text("old")

    with storage:
        storage.add(file)

    assert path.read_text() != "old"


def test_skip_if_file_exists(tmp_path: pathlib.Path, file: File) -> None:
    """It skips existing files."""
    storage = DiskFileStorage(tmp_path, fileexists=FileExistsPolicy.SKIP)

    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir()
    path.write_text("old")

    with storage:
        storage.add(file)

    assert path.read_text() == "old"
