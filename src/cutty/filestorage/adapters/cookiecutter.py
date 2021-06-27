"""Cookiecutter file storage."""
import pathlib
import platform
import shutil
import subprocess  # noqa: S404
import sys
import tempfile
from collections.abc import Iterable
from typing import Optional

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.storage import FileStorageWrapper


def _runcommand(path: pathlib.Path, *, cwd: pathlib.Path) -> None:
    command = [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
    shell = platform.system() == "Windows"
    cwd.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602


def _runhook(hooks: dict[str, File], hook: str, *, cwd: pathlib.Path) -> None:
    hookfile = hooks.get(hook)
    if hookfile is not None:
        with tempfile.TemporaryDirectory() as root:
            with DiskFileStorage(pathlib.Path(root)) as storage:
                storage.add(hookfile)
                path = storage.resolve(hookfile.path)
                _runcommand(path, cwd=cwd)


class CookiecutterFileStorage(FileStorageWrapper[DiskFileStorage]):
    """Wrap a disk-based file store with Cookiecutter hooks."""

    def __init__(
        self, storage: DiskFileStorage, *, hookfiles: Iterable[File] = ()
    ) -> None:
        """Initialize."""
        super().__init__(storage)
        self.hooks = {hook.path.stem: hook for hook in hookfiles}
        self.project: Optional[pathlib.Path] = None
        self.added = False

    def add(self, file: File) -> None:
        """Add file to storage."""
        if self.project is None:
            self.project = self.storage.resolve(file.path.parents[-2])
        if not self.added:
            _runhook(self.hooks, "pre_gen_project", cwd=self.project)
            self.added = True

        super().add(file)

    def commit(self) -> None:
        """Commit the stores."""
        if self.added:
            assert self.project is not None  # noqa: S101
            _runhook(self.hooks, "post_gen_project", cwd=self.project)

        super().commit()

    def rollback(self) -> None:
        """Roll back the stores."""
        if (
            self.project is None
            or self.storage.fileexists is FileExistsPolicy.OVERWRITE
        ):
            super().rollback()
        else:
            shutil.rmtree(self.project, ignore_errors=True)
