"""Unit tests for cutty.adapters.filesystem.files."""
import os
import pathlib
import platform

import pytest

from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.domain.files import Buffer
from cutty.domain.files import Mode
from cutty.filesystem.pure import PurePath


def test_storage(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    path = PurePath("example", "README.md")
    blob = "# example\n"
    file = Buffer(path, Mode.DEFAULT, blob)

    storage = FilesystemFileStorage(tmp_path)
    storage.store(file)

    assert blob == (tmp_path / "example" / "README.md").read_text()


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Path.chmod ignores executable bits on Windows.",
)
def test_executable(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    path = PurePath("main.py")
    blob = "#!/usr/bin/env python"
    file = Buffer(path, Mode.EXECUTABLE, blob)

    storage = FilesystemFileStorage(tmp_path)
    storage.store(file)

    assert os.access(tmp_path / "main.py", os.X_OK)


def test_temporary() -> None:
    """It creates temporary storage."""
    file = Buffer(PurePath("file"), Mode.DEFAULT, "")

    with FilesystemFileStorage.temporary() as storage:
        storage.store(file)
        path = storage.resolve(file.path)
        assert path.exists()

    assert not path.exists()
