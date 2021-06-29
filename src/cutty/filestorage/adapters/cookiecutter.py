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
from cutty.filestorage.domain.storage import FileStorageObserver


class _Hooks:
    def __init__(self, *, hookfiles: Iterable[File] = (), cwd: pathlib.Path) -> None:
        self.hooks = {hook.path.stem: hook for hook in hookfiles}
        self.cwd = cwd

    def run(self, hook: str) -> None:
        hookfile = self.hooks.get(hook)
        if hookfile is not None:
            self._runfile(hookfile)

    def _runfile(self, hookfile: File) -> None:
        with tempfile.TemporaryDirectory() as root:
            with DiskFileStorage(pathlib.Path(root)) as storage:
                storage.add(hookfile)
                path = storage.resolve(hookfile.path)
                self._runpath(path)

    def _runpath(self, path: pathlib.Path) -> None:
        command = (
            [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
        )
        shell = platform.system() == "Windows"
        self.cwd.mkdir(parents=True, exist_ok=True)
        subprocess.run(command, shell=shell, cwd=self.cwd, check=True)  # noqa: S602


class CookiecutterFileStorageObserver(FileStorageObserver):
    """Storage observer invoking Cookiecutter hooks."""

    def __init__(self, hooks: _Hooks, *, overwrite: bool) -> None:
        """Initialize."""
        self.hooks = hooks
        self.overwrite = overwrite

    def begin(self) -> None:
        """A storage transaction was started."""
        self.hooks.run("pre_gen_project")

    def commit(self) -> None:
        """A storage transaction was completed."""
        self.hooks.run("post_gen_project")

    def rollback(self) -> None:
        """A storage transaction was aborted."""
        if not self.overwrite:
            shutil.rmtree(self.hooks.cwd, ignore_errors=True)


def CookiecutterFileStorage(  # noqa: N802
    storage: DiskFileStorage, *, hookfiles: Iterable[File] = (), project: pathlib.Path
) -> DiskFileStorage:
    """Wrap a disk-based file store with Cookiecutter hooks."""
    storage.observers.append(
        CookiecutterFileStorageObserver(
            _Hooks(hookfiles=hookfiles, cwd=project),
            overwrite=storage.fileexists is FileExistsPolicy.OVERWRITE,
        )
    )
    return storage
