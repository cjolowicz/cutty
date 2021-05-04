"""File storage for Cookiecutter."""
from __future__ import annotations

import pathlib
import tempfile
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Optional

from cutty.application.cookiecutter.hooks import executehook
from cutty.compat.contextlib import contextmanager
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.domain.files import File
from cutty.templates.domain.files import Mode


class DiskFileStorage:
    """Disk-based store for files."""

    def __init__(self, root: pathlib.Path) -> None:
        """Initialize."""
        self.root = root

    def store(self, files: Iterable[File]) -> None:
        """Commit the files to storage."""
        for file in files:
            path = self.resolve(file.path)
            self.storefile(file, path)

    def storefile(self, file: File, path: pathlib.Path) -> None:
        """Commit a file to storage."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(file.blob)
        if file.mode & Mode.EXECUTABLE:
            path.chmod(path.stat().st_mode | 0o111)

    def resolve(self, path: PurePath) -> pathlib.Path:
        """Resolve the path to a filesystem location."""
        return self.root.joinpath(*path.parts)


@contextmanager
def temporarystorage() -> Iterator[DiskFileStorage]:
    """Return temporary storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(tmpdir)
        yield DiskFileStorage(path)


class CookiecutterFileStorage(DiskFileStorage):
    """Disk-based file store with pre and post hooks."""

    def __init__(
        self,
        path: pathlib.Path,
        *,
        overwrite_if_exists: bool = False,
        skip_if_file_exists: bool = False,
    ) -> None:
        """Initialize."""
        super().__init__(path)
        self.overwrite_if_exists = overwrite_if_exists
        self.skip_if_file_exists = skip_if_file_exists

    def store(self, files: Iterable[File]) -> None:
        """Store the files on disk."""
        hooks = {}
        project: Optional[pathlib.Path] = None

        for file in files:
            if file.path.parts[0] == "hooks":
                hooks[file.path.stem] = file
                continue

            if project is None:
                project = self.resolve(file.path.parents[-2])
                if not self.overwrite_if_exists and project.exists():
                    raise FileExistsError(f"{project} already exists")

                project.mkdir(parents=True, exist_ok=True)
                executehook(hooks, "pre_gen_project", cwd=project, storehook=storehook)

            path = self.resolve(file.path)
            if not (self.skip_if_file_exists and path.exists()):
                self.storefile(file, path)

        if project is not None:
            executehook(hooks, "post_gen_project", cwd=project, storehook=storehook)


@contextmanager
def storehook(hookfile: File) -> Iterator[pathlib.Path]:
    """Store the hook on disk."""
    with temporarystorage() as storage:
        path = storage.resolve(hookfile.path)
        storage.storefile(hookfile, path)
        yield path
