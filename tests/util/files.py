"""File utilities."""
import os
from pathlib import Path
from typing import Iterator
from typing import Union

from cutty.compat.contextlib import contextmanager


def _list_files_recursively(path: Path, *, exclude: frozenset[Path]) -> Iterator[Path]:
    if path in exclude:
        return

    if path.is_dir():
        for entry in path.iterdir():
            yield from _list_files_recursively(entry, exclude=exclude)
    else:
        yield path


def list_files_recursively(
    path: Path, *, exclude: frozenset[Path] = frozenset()
) -> frozenset[Path]:
    """List files starting at path, descending into subdirectories."""
    return frozenset(
        filename.relative_to(path)
        for filename in _list_files_recursively(path, exclude=exclude)
    )


def template_files(path: Union[Path, str]) -> frozenset[Path]:
    """List the project files contained in the template repository."""
    if isinstance(path, str):
        path = Path(path)

    path = next(entry for entry in path.iterdir() if entry.name.startswith("{{"))
    return list_files_recursively(path)


def project_files(path: Union[Path, str]) -> frozenset[Path]:
    """List the project files contained in the project repository."""
    if isinstance(path, str):
        path = Path(path)

    return list_files_recursively(path, exclude=frozenset({path / ".git"}))


@contextmanager
def chdir(path: Union[Path, str]) -> Iterator[None]:
    """Context manager for changing a directory."""
    cwd = Path.cwd()
    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(cwd)
