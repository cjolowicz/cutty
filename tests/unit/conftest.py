"""Unit test fixtures for cutty."""
from collections.abc import Iterator
from collections.abc import Mapping

import pytest

from cutty.domain.files import RenderableRepository
from cutty.domain.paths import Path
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.renderables import TrivialRenderable
from cutty.domain.varspecs import RenderableVariableSpecification
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType


class TrivialRenderableLoader(RenderableLoader[str]):
    """Fake a renderable loader using TrivialRenderable."""

    def load(self, text: str) -> Renderable[str]:
        """Load renderable from text."""
        return TrivialRenderable(text)


@pytest.fixture
def renderable_loader() -> RenderableLoader[str]:
    """Fixture for a renderable loader."""
    return TrivialRenderableLoader()


class FakeRenderableRepository(RenderableRepository):
    """Fake renderable repository."""

    def __init__(self, renderables: Mapping[Path, str]) -> None:
        """Initialize."""
        self.renderables = {
            path: TrivialRenderable(text) for path, text in renderables.items()
        }

    def list(self) -> Iterator[Path]:
        """Iterate over the paths where renderables are located."""
        return iter(self.renderables.keys())

    def get(self, path: Path) -> Renderable[str]:
        """Get renderable by path."""
        return self.renderables[path]


@pytest.fixture
def renderable_repository() -> RenderableRepository:
    """Fixture for a renderable loader."""
    return FakeRenderableRepository({})


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
