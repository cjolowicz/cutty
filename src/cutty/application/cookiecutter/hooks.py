"""Cookiecutter hooks."""
import pathlib
import platform
import subprocess  # noqa: S404
import sys


def runhook(path: pathlib.Path, *, cwd: pathlib.Path) -> None:
    """Run the hook."""
    command = [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
    shell = platform.system() == "Windows"

    subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602
