"""Unit tests for cutty.application.cookiecutter.files."""
import os
import pathlib
import platform

import pytest

from cutty.application.cookiecutter.files import CookiecutterFileStorage
from cutty.application.cookiecutter.files import DiskFileStorage
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.domain.files import File
from cutty.templates.domain.files import Mode


@pytest.fixture
def file() -> File:
    """Fixture for a regular file."""
    path = PurePath("example", "README.md")
    blob = "# example\n"
    return File(path, Mode.DEFAULT, blob)


@pytest.fixture
def executable() -> File:
    """Fixture for an executable file."""
    path = PurePath("example", "main.py")
    blob = "#!/usr/bin/env python"
    return File(path, Mode.EXECUTABLE, blob)


@pytest.fixture
def hook() -> File:
    """Fixture for a hook."""
    path = PurePath("hooks", "post_gen_project.py")
    blob = "print(end='', file=open('marker', mode='w'))"
    return File(path, Mode.EXECUTABLE, blob)


@pytest.fixture
def storage(tmp_path: pathlib.Path) -> DiskFileStorage:
    """Fixture for a storage."""
    return CookiecutterFileStorage(tmp_path)


def test_storage(tmp_path: pathlib.Path, file: File) -> None:
    """It stores the file."""
    storage = DiskFileStorage(tmp_path)
    storage.store([file])

    path = storage.resolve(file.path)
    assert file.blob == path.read_text()


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Path.chmod ignores executable bits on Windows.",
)
def test_executable(tmp_path: pathlib.Path, executable: File) -> None:
    """It stores the file."""
    storage = DiskFileStorage(tmp_path)
    storage.store([executable])

    path = storage.resolve(executable.path)
    assert os.access(path, os.X_OK)


def test_hooks(storage: DiskFileStorage, file: File, hook: File) -> None:
    """It executes the hook."""
    storage.store([hook, file])
    path = storage.resolve(PurePath("example", "marker"))
    assert path.is_file()


def test_no_files(storage: DiskFileStorage, hook: File) -> None:
    """It does nothing."""
    storage.store([hook])
    path = storage.resolve(PurePath("example", "marker"))
    assert not path.is_file()


def test_multiple_files(storage: DiskFileStorage, file: File, executable: File) -> None:
    """It stores all the files."""
    storage.store([executable, file])
    assert all(storage.resolve(x.path).is_file() for x in (file, executable))


def test_already_exists(storage: DiskFileStorage, file: File) -> None:
    """It raises an exception if the project already exists."""
    storage.store([file])
    with pytest.raises(Exception):
        storage.store([file])


def test_overwrite_if_exists(tmp_path: pathlib.Path, file: File) -> None:
    """It overwrites existing files."""
    storage = CookiecutterFileStorage(
        tmp_path,
        overwrite_if_exists=True,
        skip_if_file_exists=False,
    )
    path = storage.resolve(file.path)
    path.parent.mkdir()
    path.write_text("old")
    storage.store([file])
    assert path.read_text() != "old"


def test_skip_if_file_exists(tmp_path: pathlib.Path, file: File) -> None:
    """It skips existing files."""
    storage = CookiecutterFileStorage(
        tmp_path,
        overwrite_if_exists=True,
        skip_if_file_exists=True,
    )
    path = storage.resolve(file.path)
    path.parent.mkdir()
    path.write_text("old")
    storage.store([file])
    assert path.read_text() == "old"
