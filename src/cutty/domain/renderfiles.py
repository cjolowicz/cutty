"""Rendering files."""
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence

from cutty.domain.bindings import Binding
from cutty.domain.files import File
from cutty.domain.hooks import PostGenerateProject
from cutty.domain.hooks import PreGenerateProject
from cutty.domain.render import Renderer
from cutty.filesystem.path import Path
from cutty.util.bus import Bus


class InvalidPathComponent(Exception):
    """The rendered path has an invalid component."""


def withevents(files: Iterator[File], bus: Bus) -> Iterator[File]:
    """Publish the PreGenerateProject and PostGenerateProject events."""
    first = next(files)
    project = first.path.parents[-1]

    bus.events.publish(PreGenerateProject(project))

    yield first
    yield from files

    bus.events.publish(PostGenerateProject(project))


def renderfiles(
    paths: Iterable[Path], render: Renderer, bindings: Sequence[Binding], bus: Bus
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

    files = _renderfiles(paths)
    return withevents(files, bus)
