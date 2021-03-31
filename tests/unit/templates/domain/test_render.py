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
        (None, None),
        (["green-{x}"], ["green-teapot"]),
        ({"key": "{x}"}, {"key": "teapot"}),
        (PurePath("src", "{x}"), PurePath("src", "teapot")),
        (
            File(PurePath("{x}"), Mode.DEFAULT, "{x}"),
            File(PurePath("teapot"), Mode.DEFAULT, "teapot"),
        ),
    ],
)
def test_render(render: Renderer, template: object, expected: object) -> None:
    """It renders the template as expected."""
    binding = Binding("x", "teapot")

    assert expected == render(template, [binding])


def test_render_variable(render: Renderer, variable: GenericVariable[str]) -> None:
    """It renders the variable."""
    assert variable == render(variable, [])


def test_render_register_unannotated(render: Renderer) -> None:
    """It raises an exception if the type is not provided."""
    with pytest.raises(Exception):

        @render.register
        def render(value, bindings, render):  # type: ignore[no-untyped-def]
            ...
