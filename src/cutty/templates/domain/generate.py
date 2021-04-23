"""Generating files by rendering their paths and contents."""
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Optional
from typing import Union

from cutty.filesystems.domain.purepath import PurePath
from cutty.filesystems.domain.path import Access
from cutty.filesystems.domain.path import Path
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.render import Renderer


@dataclass(frozen=True)
class File:
    """A file."""

    path: PurePath


@dataclass(frozen=True)
class RegularFile(File):
    """A regular file."""

    blob: bytes


@dataclass(frozen=True)
class Executable(RegularFile):
    """An executable file."""


@dataclass(frozen=True)
class SymbolicLink(File):
    """A symbolic link."""

    target: PurePath


PathMatcher = Callable[[Path], bool]


def generatefiles(
    path: Path,
    render: Renderer,
    bindings: Sequence[Binding],
    *,
    follow_symlinks: bool = True,
    norender: Iterable[PathMatcher] = (),
) -> Iterator[File]:
    """Generate files."""

    norender = tuple(norender)

    def _generate(
        path: Path,
        current: PurePath,
        rendering: bool = True,
    ) -> Iterator[File]:
        current /= render(path.name, bindings)

        if not current.name:
            return

        if "/" in current.name or "\\" in current.name or current.name in (".", ".."):
            raise RuntimeError(
                f"invalid component {current.name!r} from {path.name!r} in {path}"
            )

        if rendering:
            rendering = not any(match(path) for match in norender)

        if not follow_symlinks and path.is_symlink():
            target = path.readlink()
            if rendering:
                target = PurePath(*(render(part, bindings) for part in target.parts))
            yield SymbolicLink(current, target)

        elif path.is_file():
            if rendering:
                text = path.read_text()
                text = render(text, bindings)
                blob = text.encode()
            else:
                blob = path.read_bytes()

            cls = Executable if path.access(Access.EXECUTE) else RegularFile
            yield cls(current, blob)

        elif path.is_dir():
            for entry in path.iterdir():
                yield from _generate(entry, rendering)

        else:  # pragma: no cover
            message = (
                "broken symlink"
                if path.is_symlink()
                else "special file"
                if path.exists()
                else "no such file"
            )
            raise RuntimeError(f"{path}: {message}")

    return _generate(path, PurePath(*path.parent.parts))
