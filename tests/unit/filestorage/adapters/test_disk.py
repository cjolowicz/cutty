"""Unit tests for cutty.filestorage.adapters.disk."""
import contextlib
import pathlib

import pytest

from cutty.filestorage.adapters.disk import diskfilestorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.adapters.disk import temporarydiskfilestorage
from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.files import SymbolicLink
from cutty.filesystems.domain.purepath import PurePath


def test_regular_file(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    file = RegularFile(PurePath("file"), b"Lorem")
    path = tmp_path.joinpath(*file.path.parts)

    with diskfilestorage(tmp_path) as storefile:
        storefile(file)

    assert path.read_bytes() == file.blob


def test_regular_file_undo(tmp_path: pathlib.Path) -> None:
    """It removes a created file when rolling back after an error."""
    file = RegularFile(PurePath("file"), b"Lorem")
    path = tmp_path.joinpath(*file.path.parts)

    class FakeError(Exception):
        pass

    with contextlib.suppress(FakeError):
        with diskfilestorage(tmp_path) as storefile:
            storefile(file)
            raise FakeError()

    assert not path.exists()


def test_directory_undo(tmp_path: pathlib.Path) -> None:
    """It removes a created directory when rolling back after an error."""
    file = RegularFile(PurePath("dir", "file"), b"Lorem")
    path = tmp_path.joinpath(*file.path.parts)

    class FakeError(Exception):
        pass

    with contextlib.suppress(FakeError):
        with diskfilestorage(tmp_path) as storefile:
            storefile(file)
            raise FakeError()

    assert not path.exists()
    assert not path.parent.exists()


def test_file_exists_raise(tmp_path: pathlib.Path) -> None:
    """It raises an exception if the file exists."""
    file = RegularFile(PurePath("file"), b"Lorem")
    path = tmp_path.joinpath(*file.path.parts)
    path.touch()

    with diskfilestorage(tmp_path) as storefile:
        with pytest.raises(FileExistsError):
            storefile(file)


def test_file_exists_skip(tmp_path: pathlib.Path) -> None:
    """It skips existing files when requested."""
    file = RegularFile(PurePath("file"), b"Lorem")
    path = tmp_path.joinpath(*file.path.parts)
    path.touch()

    with diskfilestorage(tmp_path, fileexists=FileExistsPolicy.SKIP) as storefile:
        storefile(file)

    assert not path.read_bytes()


def test_file_exists_overwrite(tmp_path: pathlib.Path) -> None:
    """It overwrites an existing file when requested."""
    file = RegularFile(PurePath("file"), b"Lorem")
    path = tmp_path.joinpath(*file.path.parts)
    path.touch()

    with diskfilestorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storefile:
        storefile(file)

    assert path.read_bytes() == file.blob


def test_file_exists_overwrite_directory(tmp_path: pathlib.Path) -> None:
    """It raises an exception if the target is an existing directory."""
    file = RegularFile(PurePath("file"), b"Lorem")
    path = tmp_path.joinpath(*file.path.parts)
    path.mkdir()

    with diskfilestorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storefile:
        with pytest.raises(IsADirectoryError):
            storefile(file)


def test_file_exists_overwrite_undo(tmp_path: pathlib.Path) -> None:
    """It does not remove overwritten files when rolling back."""
    file = RegularFile(PurePath("file"), b"Lorem")
    path = tmp_path.joinpath(*file.path.parts)
    path.touch()

    class FakeError(Exception):
        pass

    with contextlib.suppress(FakeError):
        with diskfilestorage(
            tmp_path, fileexists=FileExistsPolicy.OVERWRITE
        ) as storefile:
            storefile(file)
            raise FakeError()

    assert path.exists()


def test_executable(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    file = Executable(PurePath("script.py"), b"#!python")
    path = tmp_path.joinpath(*file.path.parts)

    with diskfilestorage(tmp_path) as storefile:
        storefile(file)

    assert path.read_bytes() == file.blob


def test_symlink(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    file = SymbolicLink(PurePath("link"), PurePath("file"))
    path = tmp_path.joinpath(*file.path.parts)

    with diskfilestorage(tmp_path) as storefile:
        storefile(file)

    assert path.readlink().parts == file.target.parts


def test_symlink_overwrite_symlink(tmp_path: pathlib.Path) -> None:
    """It raises an exception."""
    file = SymbolicLink(PurePath("link"), PurePath("file"))
    path = tmp_path.joinpath(*file.path.parts)
    path.symlink_to(tmp_path)

    with diskfilestorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storefile:
        storefile(file)

    assert path.readlink().parts == file.target.parts


def test_symlink_overwrite_file(tmp_path: pathlib.Path) -> None:
    """It raises an exception."""
    file = SymbolicLink(PurePath("link"), PurePath("file"))
    path = tmp_path.joinpath(*file.path.parts)
    path.touch()

    with diskfilestorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE) as storefile:
        with pytest.raises(FileExistsError):
            storefile(file)


def test_unknown_filetype(tmp_path: pathlib.Path) -> None:
    """It raises a TypeError."""
    file = File(PurePath("dir", "file"))
    path = tmp_path.joinpath(*file.path.parts)

    with pytest.raises(TypeError):
        with diskfilestorage(tmp_path) as storefile:
            storefile(file)

    assert not path.exists()
    assert not path.parent.exists()


def test_temporarydiskfilestorage() -> None:
    """It stores the file in a temporary directory."""
    file = RegularFile(PurePath("file"), b"Lorem")

    with temporarydiskfilestorage() as storefile:
        storefile(file)
