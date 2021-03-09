"""Unit test fixtures for cutty."""
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator

import pytest

from cutty.domain.files import File
from cutty.domain.files import FileRepository
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.renderables import TrivialRenderable
from cutty.domain.varspecs import RenderableVariableSpecification
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType
from cutty.util.bus import Bus


@pytest.fixture
def bus() -> Bus:
    """Return an event bus."""
    return Bus()


class TrivialRenderableLoader(RenderableLoader[str]):
    """Fake a renderable loader using TrivialRenderable."""

    def load(self, text: str) -> Renderable[str]:
        """Load renderable from text."""
        return TrivialRenderable(text)


@pytest.fixture
def renderable_loader() -> RenderableLoader[str]:
    """Fixture for a renderable loader."""
    return TrivialRenderableLoader()


@pytest.fixture
def specification() -> Renderable[VariableSpecification[str]]:
    """Fixture with a renderable variable specification."""
    return RenderableVariableSpecification(
        name="project",
        description="The name of the project",
        type=VariableType.STRING,
        default=TrivialRenderable("example"),
        choices=(),
        interactive=True,
    )


class FakeFileRepository(FileRepository):
    """A fake repository of files."""

    def __init__(self, files: Iterable[File]) -> None:
        """Initialize."""
        self.files = files

    def load(self) -> Iterator[File]:
        """Iterate over the files in the repository."""
        return iter(self.files)


CreateFileRepository = Callable[[Iterable[File]], FileRepository]


@pytest.fixture
def create_file_repository() -> CreateFileRepository:
    """Factory fixture for a file repository."""

    def _factory(files: Iterable[File]) -> FileRepository:
        return FakeFileRepository(files)

    return _factory
