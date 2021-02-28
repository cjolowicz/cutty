"""Loading Cookiecutter paths."""
import pathlib
from collections.abc import Iterator

from cutty.domain.paths import Path


def walkfiles(path: pathlib.Path) -> Iterator[pathlib.Path]:
    """Yield the regular files in a directory tree."""
    for entry in path.iterdir():
        if entry.is_dir():
            yield from walkfiles(entry)
        elif entry.is_file():
            yield entry
        else:  # pragma: no cover
            raise RuntimeError(f"{entry} is neither regular file nor directory")


def load(repository: pathlib.Path) -> Iterator[Path]:
    """Yield the locations of renderable files in a Cookiecutter template."""
    for path in walkfiles(repository):
        path = path.relative_to(repository)
        root = path.parts[0]
        if all(token in root for token in ("{{", "cookiecutter", "}}")):
            yield Path.fromparts(path.parts)
