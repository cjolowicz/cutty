"""Unit tests for cutty.filestorage.adapters.cookiecutter."""
import pathlib
from collections.abc import Callable
from collections.abc import Iterable

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


CreateFileStorage = Callable[[Iterable[str]], FileStorage]


@pytest.fixture
def createstorage(tmp_path: pathlib.Path) -> CreateFileStorage:
    """Factory fixture for a storage with hooks."""

    def _createstorage(hooks: Iterable[str]) -> FileStorage:
        hookfiles = [
            Executable(
                PurePath("hooks", f"{hook}.py"), f"open('{hook}', mode='w')".encode()
            )
            for hook in hooks
        ]
        storage = DiskFileStorage(tmp_path)
        return CookiecutterFileStorageWrapper.wrap(storage, hookfiles=hookfiles)

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
    file: File,
    hooks: Iterable[str],
) -> None:
    """It executes the hook."""
    storage = createstorage(hooks)

    with storage:
        storage.add(file)

    for hook in hooks:
        path = tmp_path / "example" / hook
        assert path.is_file()


def test_no_files(tmp_path: pathlib.Path, createstorage: CreateFileStorage) -> None:
    """It does nothing."""
    storage = createstorage(["post_gen_project"])

    with storage:
        pass

    path = tmp_path / "example" / "post_gen_project"
    assert not path.is_file()
