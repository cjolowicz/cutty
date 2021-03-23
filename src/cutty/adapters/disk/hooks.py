"""Disk-based implementation of cutty.domain.hooks abstractions."""
import pathlib
import platform
import subprocess  # noqa: S404
import sys
from collections.abc import Iterator

from cutty.adapters.disk.files import DiskFileStorage
from cutty.compat.contextlib import contextmanager
from cutty.domain.hooks import Hook
from cutty.domain.hooks import HookExecutor


class DiskHookExecutor(HookExecutor):
    """Disk-based hook executor."""

    def __init__(self, *, cwd: pathlib.Path) -> None:
        """Initialize."""
        self.cwd = cwd

    def execute(self, hook: Hook) -> None:
        """Execute the hook."""
        with self.store(hook) as path:
            self.run(path)

    @contextmanager
    def store(self, hook: Hook) -> Iterator[pathlib.Path]:
        """Store the hook on disk."""
        with DiskFileStorage.temporary() as storage:
            storage.store(hook.file)
            yield storage.resolve(hook.file.path)

    def run(self, path: pathlib.Path) -> None:
        """Run the hook from disk."""
        self.cwd.mkdir(parents=True, exist_ok=True)

        command = (
            [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
        )
        shell = platform.system() == "Windows"

        subprocess.run(command, shell=shell, cwd=self.cwd, check=True)  # noqa: S602
