"""Unit tests for cutty.filestorage.adapters.cookiecutter."""
import pathlib

import pytest

from cutty.filestorage.adapters.cookiecutter import cookiecutterfilestorage
from cutty.filestorage.adapters.cookiecutter import iterhooks
from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.storage import FileStoreManager
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath


@pytest.fixture
def file() -> RegularFile:
    """Fixture for a regular file."""
    path = PurePath("example", "README.md")
    blob = b"# example\n"
    return RegularFile(path, blob)


@pytest.fixture
def executable() -> Executable:
    """Fixture for an executable file."""
    path = PurePath("example", "main.py")
    blob = b"#!/usr/bin/env python"
    return Executable(path, blob)


@pytest.fixture
def storage(tmp_path: pathlib.Path) -> FileStoreManager:
    """Fixture for a storage."""
    return cookiecutterfilestorage(tmp_path)


@pytest.fixture
def storagewithhook(tmp_path: pathlib.Path) -> FileStoreManager:
    """Fixture for a storage with hooks."""
    hook = Executable(
        PurePath("hooks", "post_gen_project.py"),
        b"open('marker', mode='w')",
    )
    return cookiecutterfilestorage(tmp_path, hookfiles=[hook])


def test_hooks(
    tmp_path: pathlib.Path, storagewithhook: FileStoreManager, file: File
) -> None:
    """It executes the hook."""
    with storagewithhook as storefile:
        storefile(file)

    path = tmp_path / "example" / "marker"
    assert path.is_file()


def test_no_files(tmp_path: pathlib.Path, storagewithhook: FileStoreManager) -> None:
    """It does nothing."""
    with storagewithhook:
        pass

    path = tmp_path / "example" / "marker"
    assert not path.is_file()


def test_multiple_files(
    tmp_path: pathlib.Path, storage: FileStoreManager, file: File, executable: File
) -> None:
    """It stores all the files."""
    with storage as storefile:
        storefile(executable)
        storefile(file)

    assert all(
        tmp_path.joinpath(*each.path.parts).is_file() for each in (file, executable)
    )


def test_already_exists(storage: FileStoreManager, file: File) -> None:
    """It raises an exception if the file already exists."""
    with storage as storefile:
        storefile(file)
        with pytest.raises(Exception):
            storefile(file)


def test_overwrite_if_exists(tmp_path: pathlib.Path, file: File) -> None:
    """It overwrites existing files."""
    storage = cookiecutterfilestorage(
        tmp_path,
        overwrite_if_exists=True,
        skip_if_file_exists=False,
    )

    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir()
    path.write_text("old")

    with storage as storefile:
        storefile(file)

    assert path.read_text() != "old"


def test_skip_if_file_exists(tmp_path: pathlib.Path, file: File) -> None:
    """It skips existing files."""
    storage = cookiecutterfilestorage(
        tmp_path,
        overwrite_if_exists=True,
        skip_if_file_exists=True,
    )

    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir()
    path.write_text("old")

    with storage as storefile:
        storefile(file)

    assert path.read_text() == "old"


def test_iterhooks_none() -> None:
    """It does not yield if there is no hook directory."""
    filesystem = DictFilesystem({"{{ cookiecutter.project }}": {}})
    path = Path(filesystem=filesystem)
    paths = iterhooks(path)

    assert next(paths, None) is None


def test_iterhooks_paths() -> None:
    """It returns paths to hooks."""
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = iterhooks(path)

    assert next(paths) == path / "hooks" / "pre_gen_project.py"
    assert next(paths, None) is None


def test_iterhooks_bogus_hooks() -> None:
    """It ignores hooks with a backup extension."""
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py~": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = iterhooks(path)

    assert next(paths, None) is None
