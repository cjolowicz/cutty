"""Rendering files."""
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Optional

from cutty.domain.bindings import Binding
from cutty.domain.files import File
from cutty.domain.hooks import PostGenerateProject
from cutty.domain.hooks import PreGenerateProject
from cutty.domain.render import Renderer
from cutty.filesystem.path import Path
from cutty.util.bus import Bus


class InvalidPathComponent(Exception):
    """The rendered path has an invalid component."""


def withevents(paths: Iterable[Path], bus: Optional[Bus]) -> Iterator[Path]:
    """Publish the PreGenerateProject and PostGenerateProject events."""
    if bus is None:
        yield from paths
    else:
        paths = iter(paths)
        project = next(paths)
        bus.events.publish(PreGenerateProject(project))

        yield project
        yield from paths

        bus.events.publish(PostGenerateProject(project))


def renderfiles(
    paths: Iterable[Path],
    render: Renderer,
    bindings: Sequence[Binding],
    bus: Optional[Bus] = None,
) -> Iterator[File]:
    """Render the files."""
    for path in withevents(paths, bus):
        name = render(path, bindings).name
        if not name:
            continue

        if "/" in name or "\\" in name or name in (".", ".."):
            raise InvalidPathComponent(str(path), name)

        if path.is_file():
            yield render(File.load(path), bindings)
        elif path.is_dir():
            yield from renderfiles(path.iterdir(), render, bindings)
        else:  # pragma: no cover
            raise RuntimeError(f"{path}: not a regular file or directory")
