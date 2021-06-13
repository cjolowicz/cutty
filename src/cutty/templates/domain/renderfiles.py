"""Rendering files."""
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence

from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import loadfile
from cutty.filesystems.domain.path import Path
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.render import Renderer


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
                raise RuntimeError(
                    f"invalid component {name!r} from {path.name!r} in {path}"
                )

            if path.is_dir():
                yield from _renderfiles(path.iterdir())
            else:
                yield render(loadfile(path), bindings)

    return _renderfiles(paths)
