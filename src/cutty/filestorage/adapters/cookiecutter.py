"""Cookiecutter file storage."""
import pathlib
import platform
import subprocess  # noqa: S404
import sys
import tempfile
from collections.abc import Iterable
from typing import Optional

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.domain.files import File


def _runcommand(path: pathlib.Path, *, cwd: pathlib.Path) -> None:
    command = [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
    shell = platform.system() == "Windows"
    subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602


def _runhook(hooks: dict[str, File], hook: str, *, cwd: pathlib.Path) -> None:
    hookfile = hooks.get(hook)
    if hookfile is not None:
        with tempfile.TemporaryDirectory() as root:
            with DiskFileStorage(pathlib.Path(root)) as storage:
                storage.add(hookfile)
                path = storage.resolve(hookfile.path)
                _runcommand(path, cwd=cwd)


class CookiecutterFileStorage(DiskFileStorage):
    """Disk-based file store with Cookiecutter hooks."""

    def __init__(
        self,
        root: pathlib.Path,
        *,
        fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
        hookfiles: Iterable[File] = (),
    ):
        """Initialize."""
        super().__init__(root, fileexists=fileexists)
        self.hooks = {hook.path.stem: hook for hook in hookfiles}
        self.project: Optional[pathlib.Path] = None

    def add(self, file: File) -> None:
        """Add file to storage."""
        if self.project is None:
            self.project = super().resolve(file.path.parents[-2])
            self.project.mkdir(
                parents=True, exist_ok=self.fileexists is not FileExistsPolicy.RAISE
            )
            _runhook(self.hooks, "pre_gen_project", cwd=self.project)

        super().add(file)

    def commit(self) -> None:
        """Commit the stores."""
        if self.project is not None:
            _runhook(self.hooks, "post_gen_project", cwd=self.project)
