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
from cutty.filestorage.adapters.disk import diskfilestorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.adapters.disk import temporarydiskfilestorage
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.storage import FileStore


def _runcommand(path: pathlib.Path, *, cwd: pathlib.Path) -> None:
    command = [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
    shell = platform.system() == "Windows"
    subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602


def _runhook(hooks: dict[str, File], hook: str, *, cwd: pathlib.Path) -> None:
    hookfile = hooks.get(hook)
    if hookfile is not None:
        with temporarydiskfilestorage(
            onstore=functools.partial(_runcommand, cwd=cwd)
        ) as storefile:
            storefile(hookfile)


@contextmanager
def cookiecutterfilestorage(
    root: pathlib.Path,
    *,
    hookfiles: Iterable[File] = (),
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
) -> Iterator[FileStore]:
    """File store."""
    project: Optional[pathlib.Path] = None
    hooks = {hook.path.stem: hook for hook in hookfiles}
    fileexists = (
        FileExistsPolicy.RAISE
        if not overwrite_if_exists
        else FileExistsPolicy.SKIP
        if skip_if_file_exists
        else FileExistsPolicy.OVERWRITE
    )

    with diskfilestorage(root, fileexists=fileexists) as storefile:

        def _storefile(file: File) -> None:
            nonlocal project

            if project is None:
                project = root / file.path.parts[0]
                project.mkdir(parents=True, exist_ok=overwrite_if_exists)
                _runhook(hooks, "pre_gen_project", cwd=project)

            return storefile(file)

        yield _storefile

        if project is not None:
            _runhook(hooks, "post_gen_project", cwd=project)
