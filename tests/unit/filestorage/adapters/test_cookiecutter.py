"""Unit tests for cutty.filestorage.adapters.cookiecutter."""
import pathlib
from collections.abc import Iterable
from typing import Protocol

import pytest

from cutty.filestorage.adapters.cookiecutter import CookiecutterFileStorage
from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.purepath import PurePath


@pytest.fixture
def files() -> Iterable[File]:
    """Fixture with files to be stored."""
    return [
        RegularFile(PurePath("example", "file1"), b"data1"),
        RegularFile(PurePath("example", "file2"), b"data2"),
    ]


class CreateFileStorage(Protocol):
    """Storage factory protocol."""

    def __call__(
        self,
        hooks: Iterable[str],
        *,
        fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
    ) -> FileStorage:
        """Create the storage."""


@pytest.fixture
def createstorage(tmp_path: pathlib.Path) -> CreateFileStorage:
    """Factory fixture for a storage with hooks."""

    def _createstorage(
        hooks: Iterable[str], *, fileexists: FileExistsPolicy = FileExistsPolicy.RAISE
    ) -> FileStorage:
        storage = DiskFileStorage(tmp_path, fileexists=fileexists)
        hookfiles = [
            Executable(
                PurePath("hooks", f"{hook}.py"), f"open('{hook}', mode='w')".encode()
            )
            for hook in hooks
        ]
        if hookfiles:
            return CookiecutterFileStorage(storage, hookfiles=hookfiles)
        return storage

    return _createstorage


@pytest.mark.parametrize(
    "hooks",
    [
        ["pre_gen_project"],
        ["post_gen_project"],
        ["pre_gen_project", "post_gen_project"],
    ],
)
def test_hooks(
    tmp_path: pathlib.Path,
    createstorage: CreateFileStorage,
    files: Iterable[File],
    hooks: Iterable[str],
) -> None:
    """It executes the hook."""
    storage = createstorage(hooks)

    with storage:
        for file in files:
            storage.add(file)

    for hook in hooks:
        path = tmp_path / "example" / hook
        assert path.is_file()


def test_no_files(tmp_path: pathlib.Path, createstorage: CreateFileStorage) -> None:
    """It does nothing."""
    hooks = ["pre_gen_project", "post_gen_project"]
    storage = createstorage(hooks)

    with storage:
        pass

    for hook in hooks:
        path = tmp_path / "example" / hook
        assert not path.is_file()


def test_rollback_default(
    tmp_path: pathlib.Path, createstorage: CreateFileStorage, files: Iterable[File]
) -> None:
    """It removes any created files."""
    storage = createstorage(["pre_gen_project"])

    with pytest.raises(RuntimeError):
        with storage:
            for file in files:
                storage.add(file)
            raise RuntimeError()

    path = tmp_path / "example" / "pre_gen_project"
    assert not path.is_file()


def test_rollback_overwrite(
    tmp_path: pathlib.Path, createstorage: CreateFileStorage, files: Iterable[File]
) -> None:
    """It only removes files added to the storage."""
    storage = createstorage(["pre_gen_project"], fileexists=FileExistsPolicy.OVERWRITE)

    with pytest.raises(RuntimeError):
        with storage:
            for file in files:
                storage.add(file)
            raise RuntimeError()

    path = tmp_path / "example" / "pre_gen_project"
    assert path.is_file()
    assert not any(tmp_path.joinpath(*file.path.parts).is_file() for file in files)
