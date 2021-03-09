"""File abstraction."""
import abc
import contextlib
import enum
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from dataclasses import dataclass

from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.variables import Value
from cutty.domain.variables import Variable


class EmptyPathComponent(Exception):
    """The rendered path has an empty component."""


class InvalidPathComponent(Exception):
    """The rendered path has an invalid component."""


@dataclass(frozen=True)
class Path:
    """The location of a file within a template or project."""

    parts: tuple[str, ...]

    def __init__(self, parts: Iterable[str]) -> None:
        """Initialize."""
        parts = tuple(parts)

        for part in parts:
            if not part:
                raise EmptyPathComponent(parts, part)

            if "/" in part or "\\" in part or part == "." or part == "..":
                raise InvalidPathComponent(parts, part)

        object.__setattr__(self, "parts", parts)


class Mode(enum.Flag):
    """File mode."""

    DEFAULT = 0
    EXECUTABLE = enum.auto()


@dataclass(frozen=True)
class File:
    """A file in memory."""

    path: Path
    mode: Mode
    blob: str


class FileStorage(abc.ABC):
    """Any store for files."""

    @abc.abstractmethod
    def store(self, file: File) -> None:
        """Commit a file to storage."""


class RenderablePath(Renderable[Path]):
    """A renderable path."""

    def __init__(self, parts: Iterable[Renderable[str]]) -> None:
        """Initialize."""
        self.parts = tuple(parts)

    def render(self, variables: Sequence[Variable[Value]]) -> Path:
        """Render to a Path."""
        return Path(part.render(variables) for part in self.parts)


class RenderableFile(Renderable[File]):
    """A renderable file."""

    def __init__(self, path: RenderablePath, mode: Mode, blob: Renderable[str]) -> None:
        """Initialize."""
        self.path = path
        self.mode = mode
        self.blob = blob

    def render(self, variables: Sequence[Variable[Value]]) -> File:
        """Render to a file."""
        path = self.path.render(variables)
        blob = self.blob.render(variables)
        return File(path, self.mode, blob)


class RenderableFileLoader(RenderableLoader[File]):
    """A loader for renderable files."""

    def __init__(self, loader: RenderableLoader[str]) -> None:
        """Initialize."""
        self.loader = loader

    def load(self, file: File) -> Renderable[File]:
        """Load renderable file."""
        path = RenderablePath(self.loader.load(part) for part in file.path.parts)
        blob = self.loader.load(file.blob)
        return RenderableFile(path, file.mode, blob)


def loadfiles(
    files: Iterable[File], loader: RenderableLoader[File]
) -> Iterator[Renderable[File]]:
    """Load renderable files."""
    for file in files:
        yield loader.load(file)


def renderfiles(
    files: Iterable[Renderable[File]], variables: Sequence[Variable[Value]]
) -> Iterator[File]:
    """Render the files, skipping those with empty path components."""
    for file in files:
        with contextlib.suppress(EmptyPathComponent):
            yield file.render(variables)
