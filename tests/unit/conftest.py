"""Unit test fixtures for cutty."""
from collections.abc import Mapping

import pytest

from cutty.domain.paths import Path
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.renderables import RenderableRepository
from cutty.domain.renderables import TrivialRenderable
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType


class TrivialRenderableLoader(RenderableLoader):
    """Fake a renderable loader using TrivialRenderable."""

    def loadtext(self, text: str) -> Renderable[str]:
        """Load renderable from text."""
        return TrivialRenderable(text)


@pytest.fixture
def renderable_loader() -> RenderableLoader:
    """Fixture for a renderable loader."""
    return TrivialRenderableLoader()


class FakeRenderableRepository(RenderableRepository):
    """Fake renderable repository."""

    def __init__(self, renderables: Mapping[Path, str]) -> None:
        """Initialize."""
        self.renderables = {
            path: TrivialRenderable(text) for path, text in renderables.items()
        }

    def get(self, path: Path) -> Renderable[str]:
        """Get renderable by path."""
        return self.renderables[path]


@pytest.fixture
def renderable_repository() -> RenderableRepository:
    """Fixture for a renderable loader."""
    return FakeRenderableRepository({})


@pytest.fixture
def specification() -> VariableSpecification[Renderable[str]]:
    """Fixture with a renderable variable specification."""
    return VariableSpecification(
        name="project",
        description="The name of the project",
        type=VariableType.STRING,
        default=TrivialRenderable("example"),
        choices=(),
        interactive=True,
    )
