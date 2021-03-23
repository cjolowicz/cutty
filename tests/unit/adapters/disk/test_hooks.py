"""Unit tests for cutty.adapters.disk.hooks."""
import pathlib

import pytest

from cutty.adapters.disk.hooks import executehook
from cutty.domain.files import File
from cutty.domain.files import Mode
from cutty.filesystem.disk import DiskFilesystem
from cutty.filesystem.path import Path
from cutty.filesystem.pure import PurePath


def test_executehook(tmp_path: pathlib.Path, capfd: pytest.CaptureFixture[str]) -> None:
    """It executes the script."""
    project = Path(filesystem=DiskFilesystem(tmp_path))
    hookfile = File(PurePath("hook.py"), Mode.EXECUTABLE, 'print("hello")\n')

    executehook(hookfile, project)

    captured = capfd.readouterr()
    assert captured.out == "hello\n"
    assert captured.err == ""
