"""Unit tests for cutty.adapters.filesystem.hooks."""
import pathlib

import pytest

from cutty.adapters.filesystem.hooks import FilesystemHookExecutor
from cutty.domain.files import File
from cutty.domain.files import Mode
from cutty.domain.hooks import Hook
from cutty.domain.hooks import PostGenerateProject
from cutty.filesystem.pure import PurePath


def test_executor(tmp_path: pathlib.Path, capfd: pytest.CaptureFixture[str]) -> None:
    """It executes the script."""
    file = File(PurePath("hook.py"), Mode.EXECUTABLE, 'print("hello")\n')
    hook = Hook(file=file, event=PostGenerateProject)

    executor = FilesystemHookExecutor(cwd=tmp_path)
    executor.execute(hook)

    captured = capfd.readouterr()
    assert captured.out == "hello\n"
    assert captured.err == ""
