"""Unit test fixtures for cutty."""
import pytest

from cutty.templates.domain.render import createrenderer
from cutty.templates.domain.render import defaultrenderregistry
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.variables import GenericVariable
from cutty.util.bus import Bus


@pytest.fixture
def bus() -> Bus:
    """Return an event bus."""
    return Bus()


@pytest.fixture
def render() -> Renderer:
    """Fixture with a renderer based on ``str.format``."""

    def rendertext(value, bindings, _):  # type: ignore[no-untyped-def]
        return value.format_map({binding.name: binding.value for binding in bindings})

    return createrenderer({**defaultrenderregistry, str: rendertext})


@pytest.fixture
def variable() -> GenericVariable[str]:
    """Fixture with a variable."""
    return GenericVariable(
        name="project",
        description="The name of the project",
        type=str,
        default="example",
        choices=(),
        interactive=True,
    )
