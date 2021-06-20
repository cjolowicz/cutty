"""Unit tests for cutty.filestorage.adapters.cookiecutter."""
import pathlib

import pytest

from cutty.filestorage.adapters.cookiecutter import CookiecutterFileStorageWrapper
from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.purepath import PurePath


@pytest.fixture
def file() -> RegularFile:
    """Fixture for a regular file."""
    path = PurePath("example", "README.md")
    blob = b"# example\n"
    return RegularFile(path, blob)


@pytest.fixture
def storage(tmp_path: pathlib.Path) -> FileStorage:
    """Fixture for a storage with hooks."""
    hook = Executable(
        PurePath("hooks", "post_gen_project.py"),
        b"open('marker', mode='w')",
    )
    storage = DiskFileStorage(tmp_path)
    return CookiecutterFileStorageWrapper.wrap(storage, hookfiles=[hook])


def test_hooks(tmp_path: pathlib.Path, storage: FileStorage, file: File) -> None:
    """It executes the hook."""
    with storage:
        storage.add(file)

    path = tmp_path / "example" / "marker"
    assert path.is_file()


def test_no_files(tmp_path: pathlib.Path, storage: FileStorage) -> None:
    """It does nothing."""
    with storage:
        pass

    path = tmp_path / "example" / "marker"
    assert not path.is_file()
