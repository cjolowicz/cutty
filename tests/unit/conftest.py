"""Unit test fixtures for cutty."""
import pytest

from cutty.domain.render import Renderer
from cutty.domain.variables import ValueType
from cutty.domain.variables import Variable
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
    def _(value, bindings, settings, _):  # type: ignore[no-untyped-def]
        return value.format_map({binding.name: binding.value for binding in bindings})

    return render


@pytest.fixture
def variable() -> Variable[str]:
    """Fixture with a variable."""
    return Variable(
        name="project",
        description="The name of the project",
        type=ValueType.STRING,
        default="example",
        choices=(),
        interactive=True,
    )
