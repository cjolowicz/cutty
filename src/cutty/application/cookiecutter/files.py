"""File storage for Cookiecutter."""
from __future__ import annotations

import pathlib
import platform
import subprocess  # noqa: S404
import sys
import tempfile
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Mapping
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.templates.adapters.diskfilestorage import DiskFileStorage
from cutty.templates.domain.files import File


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

    @classmethod
    @contextmanager
    def temporary(cls) -> Iterator[CookiecutterFileStorage]:
        """Return temporary storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir)
            yield cls(path)

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
                self.executehook(hooks, "pre_gen_project", project)

            path = self.resolve(file.path)
            if not (self.skip_if_file_exists and path.exists()):
                self.storefile(file, path)

        if project is not None:
            self.executehook(hooks, "post_gen_project", project)

    def executehook(
        self, hooks: Mapping[str, File], hook: str, project: pathlib.Path
    ) -> None:
        """Execute the hook."""
        hookfile = hooks.get(hook)
        if hookfile is not None:
            with self.storehook(hookfile) as path:
                runhook(path, project)

    @classmethod
    @contextmanager
    def storehook(cls, hookfile: File) -> Iterator[pathlib.Path]:
        """Store the hook on disk."""
        with cls.temporary() as storage:
            path = storage.resolve(hookfile.path)
            storage.storefile(hookfile, path)
            yield path


def runhook(path: pathlib.Path, project: pathlib.Path) -> None:
    """Run the hook."""
    command = [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
    shell = platform.system() == "Windows"

    project.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, shell=shell, cwd=project, check=True)  # noqa: S602
