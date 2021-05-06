"""Unit tests for cutty.filestorage.adapters.disk."""
import pathlib

import pytest

from cutty.filestorage.adapters.disk import diskfilestorage
from cutty.filestorage.adapters.disk import temporarydiskfilestorage
from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.files import SymbolicLink
from cutty.filesystems.domain.purepath import PurePath


def test_regular_file(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    file = RegularFile(PurePath("file"), b"Lorem")

    with diskfilestorage(tmp_path) as storefile:
        storefile(file)

    assert (tmp_path / file.path.name).read_bytes() == file.blob


def test_executable(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    file = Executable(PurePath("script.py"), b"#!python")

    with diskfilestorage(tmp_path) as storefile:
        storefile(file)

    assert (tmp_path / file.path.name).read_bytes() == file.blob


def test_symbolic_link(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    file = SymbolicLink(PurePath("link"), PurePath("file"))

    with diskfilestorage(tmp_path) as storefile:
        storefile(file)

    assert (tmp_path / file.path.name).readlink().parts == file.target.parts


def test_unknown_file(tmp_path: pathlib.Path) -> None:
    """It raises a TypeError."""
    file = File(PurePath("dir", "file"))

    with diskfilestorage(tmp_path) as storefile:
        with pytest.raises(TypeError):
            storefile(file)


def test_temporary_store() -> None:
    """It stores the file temporarily."""
    file = RegularFile(PurePath("file"), b"Lorem")

    with temporarydiskfilestorage() as storefile:
        storefile(file)
