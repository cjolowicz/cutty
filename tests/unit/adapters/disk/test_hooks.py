"""Unit tests for cutty.adapters.disk.hooks."""
import pathlib

import pytest

from cutty.adapters.disk.hooks import DiskHookExecutor
from cutty.domain.files import File
from cutty.domain.files import Mode
from cutty.domain.hooks import Hook
from cutty.domain.hooks import PostGenerateProject
from cutty.filesystem.disk import DiskFilesystem
from cutty.filesystem.path import Path
from cutty.filesystem.pure import PurePath


def test_executor(tmp_path: pathlib.Path, capfd: pytest.CaptureFixture[str]) -> None:
    """It executes the script."""
    file = File(PurePath("hook.py"), Mode.EXECUTABLE, 'print("hello")\n')
    hook = Hook(file=file, event=PostGenerateProject)

    executor = DiskHookExecutor()
    executor.execute(hook, Path(filesystem=DiskFilesystem(tmp_path)))

    captured = capfd.readouterr()
    assert captured.out == "hello\n"
    assert captured.err == ""
