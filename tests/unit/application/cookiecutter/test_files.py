"""Unit tests for cutty.application.cookiecutter.files."""
import os
import pathlib
import platform

import pytest

from cutty.application.cookiecutter.files import DiskFileStorage
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.domain.files import File
from cutty.templates.domain.files import Mode


def test_storage(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    path = PurePath("example", "README.md")
    blob = "# example\n"
    file = File(path, Mode.DEFAULT, blob)

    storage = DiskFileStorage(tmp_path)
    storage.store([file])

    assert blob == (tmp_path / "example" / "README.md").read_text()


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Path.chmod ignores executable bits on Windows.",
)
def test_executable(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    path = PurePath("main.py")
    blob = "#!/usr/bin/env python"
    file = File(path, Mode.EXECUTABLE, blob)

    storage = DiskFileStorage(tmp_path)
    storage.store([file])

    assert os.access(tmp_path / "main.py", os.X_OK)
