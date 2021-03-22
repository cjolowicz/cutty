"""Templates."""
import contextlib
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence

from cutty.domain.bindings import Binding
from cutty.domain.files import File
from cutty.domain.render import Renderer


class EmptyPathComponent(Exception):
    """The rendered path has an empty component."""


class InvalidPathComponent(Exception):
    """The rendered path has an invalid component."""


def renderfiles(
    files: Iterable[File], *, render: Renderer, bindings: Sequence[Binding]
) -> Iterator[File]:
    """Render the template."""
    for file in files:
        with contextlib.suppress(EmptyPathComponent):
            yield renderfile(file, render=render, bindings=bindings)


def renderfile(file: File, *, render: Renderer, bindings: Sequence[Binding]) -> File:
    """Render the file."""
    file = render(file, bindings)

    if not all(file.path.parts):
        # FIXME: Shouldn't have rendered the blob at all.
        # FIXME: Can we avoid traversing that directory?
        raise EmptyPathComponent(str(file.path))

    if any(
        "/" in part or "\\" in part or part == "." or part == ".."
        for part in file.path.parts
    ):
        raise InvalidPathComponent(str(file.path))

    return file
