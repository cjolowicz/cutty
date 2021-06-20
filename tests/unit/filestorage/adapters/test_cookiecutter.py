"""Unit tests for cutty.filestorage.adapters.cookiecutter."""
import pathlib
from collections.abc import Iterable

import pytest

from cutty.filestorage.adapters.cookiecutter import CookiecutterFileStorageWrapper
from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.purepath import PurePath


def CookiecutterFileStorage(  # noqa: N802
    root: pathlib.Path,
    *,
    fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
    hookfiles: Iterable[File] = (),
) -> FileStorage:
    """Disk-based file store with Cookiecutter hooks."""
    storage = DiskFileStorage(root, fileexists=fileexists)
    return CookiecutterFileStorageWrapper.wrap(storage, hookfiles=hookfiles)


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
def storage(tmp_path: pathlib.Path) -> FileStorage:
    """Fixture for a storage."""
    return CookiecutterFileStorage(tmp_path)


@pytest.fixture
def storagewithhook(tmp_path: pathlib.Path) -> FileStorage:
    """Fixture for a storage with hooks."""
    hook = Executable(
        PurePath("hooks", "post_gen_project.py"),
        b"open('marker', mode='w')",
    )
    return CookiecutterFileStorage(tmp_path, hookfiles=[hook])


def test_hooks(
    tmp_path: pathlib.Path, storagewithhook: FileStorage, file: File
) -> None:
    """It executes the hook."""
    with storagewithhook:
        storagewithhook.add(file)

    path = tmp_path / "example" / "marker"
    assert path.is_file()


def test_no_files(tmp_path: pathlib.Path, storagewithhook: FileStorage) -> None:
    """It does nothing."""
    with storagewithhook:
        pass

    path = tmp_path / "example" / "marker"
    assert not path.is_file()


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
    storage = CookiecutterFileStorage(tmp_path, fileexists=FileExistsPolicy.OVERWRITE)

    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir()
    path.write_text("old")

    with storage:
        storage.add(file)

    assert path.read_text() != "old"


def test_skip_if_file_exists(tmp_path: pathlib.Path, file: File) -> None:
    """It skips existing files."""
    storage = CookiecutterFileStorage(tmp_path, fileexists=FileExistsPolicy.SKIP)

    path = tmp_path.joinpath(*file.path.parts)
    path.parent.mkdir()
    path.write_text("old")

    with storage:
        storage.add(file)

    assert path.read_text() == "old"
