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


class RenderableRepository(abc.ABC):
    """Load renderables from paths."""

    @abc.abstractmethod
    def list(self) -> Iterator[Path]:
        """Iterate over the paths where renderables are located."""

    @abc.abstractmethod
    def get(self, path: Path) -> Renderable[str]:
        """Get renderable by path."""


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
        return Path(part.render(variables) for part in self.parts)


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


class RenderableFileRepository(abc.ABC):
    """A repository of renderable files."""

    @abc.abstractmethod
    def load(self) -> Iterator[Renderable[File]]:
        """Load renderable files."""


class DefaultRenderableFileRepository(RenderableFileRepository):
    """A repository of renderable files (default implementation)."""

    def __init__(
        self,
        loader: RenderableLoader[str],
        repository: RenderableRepository,
    ) -> None:
        """Initialize."""
        self.loader = loader
        self.repository = repository

    def load(self) -> Iterator[Renderable[File]]:
        """Load renderable files."""
        for path in self.repository.list():
            yield RenderableFile(
                RenderablePath(self.loader.load(part) for part in path.parts),
                self.repository.get(path),
            )
