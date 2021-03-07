"""File abstraction."""
import abc
import enum
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from dataclasses import dataclass

from cutty.domain.paths import Path
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.variables import Value
from cutty.domain.variables import Variable


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


class FileRepository(abc.ABC):
    """A repository of files."""

    @abc.abstractmethod
    def load(self) -> Iterator[File]:
        """Iterate over the files in the repository."""


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


class RenderableFileRepository(abc.ABC):
    """A repository of renderable files."""

    def __init__(
        self,
        repository: FileRepository,
        loader: RenderableLoader[File],
    ) -> None:
        """Initialize."""
        self.repository = repository
        self.loader = loader

    def load(self) -> Iterator[Renderable[File]]:
        """Load renderable files."""
        for file in self.repository.load():
            yield self.loader.load(file)
