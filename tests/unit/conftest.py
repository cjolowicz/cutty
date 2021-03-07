"""Unit test fixtures for cutty."""
import pytest

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
