"""Filesystem implementation of the cutty.domain.hooks abstractions."""
import pathlib
import platform
import subprocess  # noqa: S404
import sys

from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.domain.hooks import Hook
from cutty.domain.hooks import HookExecutor


class FilesystemHookExecutor(HookExecutor):
    """Filesystem-based hook executor."""

    def __init__(self, *, storage: FilesystemFileStorage, cwd: pathlib.Path) -> None:
        """Initialize."""
        self.storage = storage
        self.cwd = cwd

    def execute(self, hook: Hook) -> None:
        """Execute the hook."""
        path = self.store(hook)
        self.run(path)

    def store(self, hook: Hook) -> pathlib.Path:
        """Store the hook in the filesystem."""
        self.storage.store(hook.file)
        return self.storage.resolve(hook.file.path)

    def run(self, path: pathlib.Path) -> None:
        """Run the hook from the filesystem."""
        self.cwd.mkdir(parents=True, exist_ok=True)

        command = (
            [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
        )
        shell = platform.system() == "Windows"

        subprocess.run(command, shell=shell, cwd=self.cwd, check=True)  # noqa: S602
