"""Unit tests for cutty.domain.render."""
import pytest

from cutty.domain.render import Renderer
from cutty.domain.variables import Variable
from cutty.filesystem.pure import PurePath


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


@pytest.mark.parametrize(
    "template,expected",
    [
        (["green-{x}"], ["green-teapot"]),
        ({"key": "{x}"}, {"key": "teapot"}),
        (PurePath("src", "{x}"), PurePath("src", "teapot")),
    ],
)
def test_render(render: Renderer, template: object, expected: object) -> None:
    """It renders the template as expected."""
    variable = Variable("x", "teapot")

    assert expected == render(template, [variable], [])
