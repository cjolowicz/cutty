"""Unit tests for cutty.templates.domain.render."""
import pytest

from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.files import File
from cutty.templates.domain.files import Mode
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.variables import GenericVariable


@pytest.mark.parametrize(
    "template,expected",
    [
        (PurePath("src", "{x}"), PurePath("src", "teapot")),
        (
            File(PurePath("{x}"), Mode.DEFAULT, "{x}"),
            File(PurePath("teapot"), Mode.DEFAULT, "teapot"),
        ),
    ],
)
def test_render_valid(render: Renderer, template: object, expected: object) -> None:
    """It renders the template as expected."""
    binding = Binding("x", "teapot")

    assert expected == render(template, [binding])


@pytest.mark.parametrize("template", [None])
def test_render_invalid(render: Renderer, template: object) -> None:
    """It raises NotImplementedError."""
    binding = Binding("x", "teapot")

    with pytest.raises(NotImplementedError):
        render(template, [binding])


def test_render_variable(render: Renderer, variable: GenericVariable[str]) -> None:
    """It renders the variable."""
    assert variable == render(variable, [])
