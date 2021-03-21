"""Unit test fixtures for cutty."""
import pytest

from cutty.domain.render import Renderer
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType
from cutty.util.bus import Bus


@pytest.fixture
def bus() -> Bus:
    """Return an event bus."""
    return Bus()


@pytest.fixture
def render() -> Renderer:
    """Fixture with a renderer based on ``str.format``."""
    render = Renderer.create()

    @render.register(str)
    def _(value, variables, settings, _):  # type: ignore[no-untyped-def]
        return value.format_map(
            {variable.name: variable.value for variable in variables}
        )

    return render


@pytest.fixture
def specification() -> VariableSpecification[str]:
    """Fixture with a variable specification."""
    return VariableSpecification(
        name="project",
        description="The name of the project",
        type=VariableType.STRING,
        default="example",
        choices=(),
        interactive=True,
    )
