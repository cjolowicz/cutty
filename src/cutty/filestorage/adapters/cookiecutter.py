"""Cookiecutter file storage."""
import pathlib
import platform
import shutil
import subprocess  # noqa: S404
import sys
import tempfile
from collections.abc import Iterable

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.storage import FileStorageWrapper


class _Hooks:
    def __init__(self, *, hookfiles: Iterable[File] = (), cwd: pathlib.Path) -> None:
        self.hooks = {hook.path.stem: hook for hook in hookfiles}
        self.cwd = cwd

    def _runhook(self, hook: str) -> None:
        hookfile = self.hooks.get(hook)
        if hookfile is not None:
            with tempfile.TemporaryDirectory() as root:
                with DiskFileStorage(pathlib.Path(root)) as storage:
                    storage.add(hookfile)
                    path = storage.resolve(hookfile.path)
                    self._runcommand(path, cwd=self.cwd)

    def _runcommand(self, path: pathlib.Path, *, cwd: pathlib.Path) -> None:
        command = (
            [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
        )
        shell = platform.system() == "Windows"
        cwd.mkdir(parents=True, exist_ok=True)
        subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602


class CookiecutterFileStorage(FileStorageWrapper[DiskFileStorage]):
    """Wrap a disk-based file store with Cookiecutter hooks."""

    def __init__(
        self,
        storage: DiskFileStorage,
        *,
        hookfiles: Iterable[File] = (),
        project: pathlib.Path
    ) -> None:
        """Initialize."""
        super().__init__(storage)
        self.hooks = _Hooks(hookfiles=hookfiles, cwd=project)
        self.added = False

    def add(self, file: File) -> None:
        """Add file to storage."""
        if not self.added:
            self.hooks._runhook("pre_gen_project")
            self.added = True

        super().add(file)

    def commit(self) -> None:
        """Commit the stores."""
        if self.added:
            self.hooks._runhook("post_gen_project")

        super().commit()

    def rollback(self) -> None:
        """Roll back the stores."""
        super().rollback()

        if self.storage.fileexists is not FileExistsPolicy.OVERWRITE:
            shutil.rmtree(self.hooks.cwd, ignore_errors=True)
