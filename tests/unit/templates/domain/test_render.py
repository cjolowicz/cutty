"""Unit tests for cutty.templates.domain.render."""
import pytest

from cutty.filesystem.pure import PurePath
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.render import Renderer


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
    binding = Binding("x", "teapot")

    assert expected == render(template, [binding])
