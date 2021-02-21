"""Common fixtures for cutty.domain."""
import pytest

from cutty.domain.renderables import Renderable
from cutty.domain.renderables import TrivialRenderable
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType


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
