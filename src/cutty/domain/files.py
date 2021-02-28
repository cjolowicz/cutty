"""File abstraction."""
import abc
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from dataclasses import dataclass

from cutty.domain.paths import Path
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.variables import Value
from cutty.domain.variables import Variable


@dataclass(frozen=True)
class File:
    """A file in memory."""

    path: Path
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
        return Path.fromparts(part.render(variables) for part in self.parts)


class RenderableFile(Renderable[File]):
    """A renderable file."""

    def __init__(self, path: RenderablePath, blob: Renderable[str]) -> None:
        """Initialize."""
        self.path = path
        self.blob = blob

    def render(self, variables: Sequence[Variable[Value]]) -> File:
        """Render to a file."""
        path = self.path.render(variables)
        blob = self.blob.render(variables)
        return File(path, blob)


class RenderableFileLoader:
    """A loader for renderable files."""

    def __init__(self, loader: RenderableLoader) -> None:
        """Initialize."""
        self.loader = loader

    def load(self, paths: Iterable[Path]) -> Iterator[RenderableFile]:
        """Load renderable files."""
        for path in paths:
            yield self.loadfile(path)

    def loadfile(self, path: Path) -> RenderableFile:
        """Load a renderable file."""
        return RenderableFile(
            RenderablePath(self.loader.loadtext(part) for part in path.parts),
            self.loader.get(path),
        )
