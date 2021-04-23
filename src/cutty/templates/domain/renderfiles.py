"""Rendering files."""
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Optional

from cutty.filesystems.domain.path import Path
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.files import File
from cutty.templates.domain.render import Renderer


Matcher = Callable[[Path], bool]


def loadfiles(
    paths: Iterable[Path],
    *,
    match: Optional[Matcher] = None,
) -> Iterator[File]:
    """Load files from paths, recursively."""
    for path in paths:
        if match is not None and not match(path):
            continue

        if path.is_file():
            yield File.load(path)
        elif path.is_dir():
            yield from loadfiles(path.iterdir(), match=match)
        else:  # pragma: no cover
            message = "broken link" if path.is_symlink() else "special file"
            raise RuntimeError(f"{path}: {message}")


def renderfiles(
    paths: Iterable[Path], render: Renderer, bindings: Sequence[Binding]
) -> Iterator[File]:
    """Render the files."""

    def _match(path: Path) -> bool:
        path = render(path, bindings)
        for part in path.parts:
            if not part:
                return False

            if "/" in part or "\\" in part or part in (".", ".."):
                raise RuntimeError(f"{path}: invalid path component {part!r}")

        return True

    for file in loadfiles(paths, match=_match):
        yield render(file, bindings)
