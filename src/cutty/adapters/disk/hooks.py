"""Disk-based implementation of cutty.domain.hooks abstractions."""
import pathlib
import platform
import subprocess  # noqa: S404
import sys
from collections.abc import Iterator

from cutty.adapters.disk.files import DiskFileStorage
from cutty.compat.contextlib import contextmanager
from cutty.domain.hooks import Hook
from cutty.filesystem.disk import DiskFilesystem
from cutty.filesystem.path import Path


def executehook(hook: Hook, project: Path) -> None:
    """Disk-based hook executor."""
    with store(hook) as path:
        run(path, resolve(project))


def resolve(path: Path) -> pathlib.Path:
    """Resolve a disk-based path."""
    # NOTE: This function assumes that the project is written to disk
    # (precondition). In other words, disk-based hooks _must_ be used with
    # disk-based project storage.

    filesystem = path._filesystem
    assert isinstance(filesystem, DiskFilesystem)  # noqa: S101
    return filesystem.resolve(path)


@contextmanager
def store(hook: Hook) -> Iterator[pathlib.Path]:
    """Store the hook on disk."""
    with DiskFileStorage.temporary() as storage:
        storage.store(hook.file)
        yield storage.resolve(hook.file.path)


def run(path: pathlib.Path, project: pathlib.Path) -> None:
    """Run the hook from disk."""
    project.mkdir(parents=True, exist_ok=True)

    command = [pathlib.Path(sys.executable), path] if path.suffix == ".py" else [path]
    shell = platform.system() == "Windows"

    subprocess.run(command, shell=shell, cwd=project, check=True)  # noqa: S602
