"""Unit tests for cutty.adapters.filesystem.files."""
import pathlib
import platform

import pytest

from cutty.adapters.filesystem.files import FilesystemFileRepository
from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.domain.files import File
from cutty.domain.files import Mode
from cutty.domain.files import Path


def test_storage(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    path = Path(["example", "README.md"])
    blob = "# example\n"
    file = File(path, Mode.DEFAULT, blob)

    storage = FilesystemFileStorage(tmp_path)
    storage.store(file)

    assert blob == (tmp_path / "example" / "README.md").read_text()


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Path.chmod ignores executable bits on Windows.",
)
def test_executable(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    path = Path(["main.py"])
    blob = "#!/usr/bin/env python"
    file = File(path, Mode.EXECUTABLE, blob)

    storage = FilesystemFileStorage(tmp_path)
    storage.store(file)

    repository = FilesystemFileRepository(tmp_path / "main.py", relative_to=tmp_path)
    [file] = repository.load()
    assert file.mode & Mode.EXECUTABLE


def test_temporary() -> None:
    """It creates temporary storage."""
    file = File(Path(["file"]), Mode.DEFAULT, "")

    with FilesystemFileStorage.temporary() as storage:
        storage.store(file)
        path = storage.resolve(file.path)
        assert path.exists()

    assert not path.exists()
