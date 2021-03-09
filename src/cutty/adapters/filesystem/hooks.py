"""Filesystem implementation of the cutty.domain.hooks abstractions."""
import contextlib
import pathlib
import platform
import subprocess  # noqa: S404
import sys
from collections.abc import Iterator

from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.domain.hooks import Hook
from cutty.domain.hooks import HookExecutor


class FilesystemHookExecutor(HookExecutor):
    """Filesystem-based hook executor."""

    def __init__(self, *, cwd: pathlib.Path) -> None:
        """Initialize."""
        self.cwd = cwd

    def execute(self, hook: Hook) -> None:
        """Execute the hook."""
        with self.store(hook) as path:
            self.run(path)

    @contextlib.contextmanager
    def store(self, hook: Hook) -> Iterator[pathlib.Path]:
        """Store the hook in the filesystem."""
        with FilesystemFileStorage.temporary() as storage:
            storage.store(hook.file)
            yield storage.resolve(hook.file.path)

    def run(self, path: pathlib.Path) -> None:
        """Run the hook from the filesystem."""
        self.cwd.mkdir(parents=True, exist_ok=True)

        command = (
            [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
        )
        shell = platform.system() == "Windows"

        subprocess.run(command, shell=shell, cwd=self.cwd, check=True)  # noqa: S602
