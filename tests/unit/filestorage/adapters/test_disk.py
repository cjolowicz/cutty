"""Unit tests for cutty.filestorage.adapters.disk."""
import contextlib
import os
import pathlib
import platform

import pytest

from cutty.filestorage.adapters.disk import diskfilestorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.adapters.disk import temporarydiskfilestorage
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


def test_regular_file(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It stores the file."""
    with diskfilestorage(tmp_path) as storefile:
        storefile(file)

    path = tmp_path.joinpath(*file.path.parts)
    assert path.read_bytes() == file.blob


class FakeError(Exception):
    """Exception used for testing rollback."""


def test_regular_file_undo(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It removes a created file when rolling back after an error."""
    with contextlib.suppress(FakeError):
        with diskfilestorage(tmp_path) as storefile:
            storefile(file)
            raise FakeError()

    path = tmp_path.joinpath(*file.path.parts)
    assert not path.exists()


def test_directory_undo(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It removes a created directory when rolling back after an error."""
    with contextlib.suppress(FakeError):
        with diskfilestorage(tmp_path) as storefile:
            storefile(file)
            raise FakeError()

    path = tmp_path.joinpath(*file.path.parts)
    assert not path.exists()
    assert not path.parent.exists()


def test_file_exists_raise(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It raises an exception if the file exists."""
    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir(parents=True)
    path.touch()

    with diskfilestorage(tmp_path) as storefile:
        with pytest.raises(FileExistsError):
            storefile(file)


def test_file_exists_skip(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It skips existing files when requested."""
    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir(parents=True)
    path.touch()

    with diskfilestorage(tmp_path, fileexists=FileExistsPolicy.SKIP) as storefile:
        storefile(file)

    assert not path.read_bytes()


def test_file_exists_overwrite(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It overwrites an existing file when requested."""
    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir(parents=True)
    path.touch()

    with diskfilestorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storefile:
        storefile(file)

    assert path.read_bytes() == file.blob


def test_file_exists_overwrite_directory(
    tmp_path: pathlib.Path, file: RegularFile
) -> None:
    """It raises an exception if the target is an existing directory."""
    path = tmp_path.joinpath(*file.path.parts)
    path.mkdir(parents=True)

    with diskfilestorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storefile:
        error = PermissionError if platform.system() == "Windows" else IsADirectoryError
        with pytest.raises(error):
            storefile(file)


def test_file_exists_overwrite_undo(tmp_path: pathlib.Path, file: RegularFile) -> None:
    """It does not remove overwritten files when rolling back."""
    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir(parents=True)
    path.touch()

    with contextlib.suppress(FakeError):
        with diskfilestorage(
            tmp_path, fileexists=FileExistsPolicy.OVERWRITE
        ) as storefile:
            storefile(file)
            raise FakeError()

    assert path.exists()


def test_executable_blob(tmp_path: pathlib.Path, executable: Executable) -> None:
    """It stores the file."""
    with diskfilestorage(tmp_path) as storefile:
        storefile(executable)

    path = tmp_path.joinpath(*executable.path.parts)
    assert path.read_bytes() == executable.blob


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Path.chmod ignores executable bits on Windows.",
)
def test_executable_mode(tmp_path: pathlib.Path, executable: File) -> None:
    """It stores the file."""
    with diskfilestorage(tmp_path) as storefile:
        storefile(executable)

    path = tmp_path.joinpath(*executable.path.parts)
    assert os.access(path, os.X_OK)


def test_symlink(tmp_path: pathlib.Path, symlink: SymbolicLink) -> None:
    """It stores the file."""
    with diskfilestorage(tmp_path) as storefile:
        storefile(symlink)

    path = tmp_path.joinpath(*symlink.path.parts)
    assert path.readlink().parts == symlink.target.parts


def test_symlink_overwrite_symlink(
    tmp_path: pathlib.Path, symlink: SymbolicLink
) -> None:
    """It raises an exception."""
    path = tmp_path.joinpath(*symlink.path.parts)
    path.symlink_to(tmp_path)

    with diskfilestorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storefile:
        storefile(symlink)

    assert path.readlink().parts == symlink.target.parts


def test_symlink_overwrite_file(tmp_path: pathlib.Path, symlink: SymbolicLink) -> None:
    """It raises an exception."""
    path = tmp_path.joinpath(*symlink.path.parts)
    path.touch()

    with diskfilestorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storefile:
        with pytest.raises(FileExistsError):
            storefile(symlink)


def test_unknown_filetype(tmp_path: pathlib.Path) -> None:
    """It raises a TypeError."""
    file = File(PurePath("dir", "file"))

    with pytest.raises(TypeError):
        with diskfilestorage(tmp_path) as storefile:
            storefile(file)

    path = tmp_path.joinpath(*file.path.parts)
    assert not path.exists()
    assert not path.parent.exists()


def test_temporarydiskfilestorage(file: RegularFile) -> None:
    """It stores the file in a temporary directory."""
    with temporarydiskfilestorage() as storefile:
        storefile(file)
