"""Cookiecutter file storage."""
import functools
import pathlib
import platform
import subprocess  # noqa: S404
import sys
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.adapters.disk import TemporaryDiskFileStorage
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.storage import FileStore


def _runcommand(path: pathlib.Path, *, cwd: pathlib.Path) -> None:
    command = [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
    shell = platform.system() == "Windows"
    subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602


def _runhook(hooks: dict[str, File], hook: str, *, cwd: pathlib.Path) -> None:
    hookfile = hooks.get(hook)
    if hookfile is not None:
        with TemporaryDiskFileStorage(
            onstore=functools.partial(_runcommand, cwd=cwd)
        ) as storage:
            storage.add(hookfile)


class CookiecutterFileStorage(DiskFileStorage):
    """Disk-based file store with Cookiecutter hooks."""

    def __init__(
        self,
        root: pathlib.Path,
        *,
        hookfiles: Iterable[File] = (),
        overwrite_if_exists: bool = False,
        skip_if_file_exists: bool = False,
    ):
        """Initialize."""
        fileexists = (
            FileExistsPolicy.RAISE
            if not overwrite_if_exists
            else FileExistsPolicy.SKIP
            if skip_if_file_exists
            else FileExistsPolicy.OVERWRITE
        )
        super().__init__(root, fileexists=fileexists)
        self.hooks = {hook.path.stem: hook for hook in hookfiles}
        self.project: Optional[pathlib.Path] = None
        self.overwrite_if_exists = overwrite_if_exists

    def add(self, file: File) -> None:
        """Add file to storage."""
        if self.project is None:
            self.project = self.root / file.path.parts[0]
            self.project.mkdir(
                parents=True, exist_ok=self.fileexists is not FileExistsPolicy.RAISE
            )
            _runhook(self.hooks, "pre_gen_project", cwd=self.project)

        super().add(file)

    def commit(self) -> None:
        """Commit the stores."""
        if self.project is not None:
            _runhook(self.hooks, "post_gen_project", cwd=self.project)


@contextmanager
def cookiecutterfilestorage(
    root: pathlib.Path,
    *,
    hookfiles: Iterable[File] = (),
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
) -> Iterator[FileStore]:
    """File store."""
    with CookiecutterFileStorage(
        root,
        hookfiles=hookfiles,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
    ) as storage:
        yield storage.add
