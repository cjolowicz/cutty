"""Rendering files."""
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence

from cutty.filesystems.domain.path import Path
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.files import File
from cutty.templates.domain.render import Renderer


class InvalidPathComponent(Exception):
    """The rendered path has an invalid component."""


def renderfiles(
    paths: Iterable[Path], render: Renderer, bindings: Sequence[Binding]
) -> Iterator[File]:
    """Render the files."""

    def _renderfiles(paths: Iterable[Path]) -> Iterator[File]:
        for path in paths:
            name = render(path, bindings).name
            if not name:
                continue

            if "/" in name or "\\" in name or name in (".", ".."):
                raise InvalidPathComponent(str(path), name)

            if path.is_file():
                yield render(File.load(path), bindings)
            elif path.is_dir():
                yield from _renderfiles(path.iterdir())
            else:  # pragma: no cover
                raise RuntimeError(f"{path}: not a regular file or directory")

    return _renderfiles(paths)
