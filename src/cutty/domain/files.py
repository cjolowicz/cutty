"""File abstraction."""
import abc
import contextlib
import enum
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from dataclasses import dataclass

from cutty.domain.filesystem import PurePath
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.variables import Value
from cutty.domain.variables import Variable


class Mode(enum.Flag):
    """File mode."""

    DEFAULT = 0
    EXECUTABLE = enum.auto()


class File(abc.ABC):
    """File abstraction."""

    @property
    @abc.abstractmethod
    def path(self) -> PurePath:
        """Return the file path."""

    @property
    @abc.abstractmethod
    def mode(self) -> Mode:
        """Return the file mode."""

    @abc.abstractmethod
    def read(self) -> str:
        """Return the file contents."""


@dataclass(frozen=True)
class Buffer(File):
    """A file in memory."""

    _path: PurePath
    _mode: Mode
    _blob: str

    @property
    def path(self) -> PurePath:
        """Return the file path."""
        return self._path

    @property
    def mode(self) -> Mode:
        """Return the file mode."""
        return self._mode

    def read(self) -> str:
        """Return the file contents."""
        return self._blob


class FileStorage(abc.ABC):
    """Any store for files."""

    @abc.abstractmethod
    def store(self, file: File) -> None:
        """Commit a file to storage."""


class EmptyPathComponent(Exception):
    """The rendered path has an empty component."""


class InvalidPathComponent(Exception):
    """The rendered path has an invalid component."""


class RenderablePath(Renderable[PurePath]):
    """A renderable path."""

    def __init__(self, parts: Iterable[Renderable[str]]) -> None:
        """Initialize."""
        self.parts = tuple(parts)

    def render(self, variables: Sequence[Variable[Value]]) -> PurePath:
        """Render to a PurePath."""

        def _iterparts() -> Iterator[str]:
            for renderable in self.parts:
                part = renderable.render(variables)

                if not part:
                    raise EmptyPathComponent()

                if "/" in part or "\\" in part or part == "." or part == "..":
                    raise InvalidPathComponent(part)

                yield part

        return PurePath(*_iterparts())


class RenderableBuffer(Renderable[Buffer]):
    """A renderable buffer."""

    def __init__(self, path: RenderablePath, mode: Mode, blob: Renderable[str]) -> None:
        """Initialize."""
        self.path = path
        self.mode = mode
        self.blob = blob

    def render(self, variables: Sequence[Variable[Value]]) -> Buffer:
        """Render to a file."""
        path = self.path.render(variables)
        blob = self.blob.render(variables)
        return Buffer(path, self.mode, blob)


class RenderableFileLoader(RenderableLoader[File]):
    """A loader for renderable files."""

    def __init__(self, loader: RenderableLoader[str]) -> None:
        """Initialize."""
        self.loader = loader

    def load(self, file: File) -> Renderable[File]:
        """Load renderable file."""
        path = RenderablePath(self.loader.load(part) for part in file.path.parts)
        blob = self.loader.load(file.read())
        return RenderableBuffer(path, file.mode, blob)


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
