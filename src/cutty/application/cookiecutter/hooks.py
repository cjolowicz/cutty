"""Cookiecutter hooks."""
import pathlib
import platform
import subprocess  # noqa: S404
import sys
from collections.abc import Callable
from collections.abc import Mapping
from contextlib import AbstractContextManager

from cutty.templates.domain.files import File


def executehook(
    hooks: Mapping[str, File],
    hook: str,
    *,
    cwd: pathlib.Path,
    storehook: Callable[[File], AbstractContextManager[pathlib.Path]]
) -> None:
    """Execute the hook."""
    hookfile = hooks.get(hook)
    if hookfile is not None:
        with storehook(hookfile) as path:
            runhook(path, cwd=cwd)


def runhook(path: pathlib.Path, *, cwd: pathlib.Path) -> None:
    """Run the hook."""
    command = [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
    shell = platform.system() == "Windows"

    subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602
