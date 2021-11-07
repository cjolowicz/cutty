"""Unit tests for cutty.templates.domain.bindvariables."""
import pytest

from cutty.templates.domain.bindvariables import renderbind
from cutty.templates.domain.render import Renderer
from cutty.variables.binders import binddefault
from cutty.variables.binders import override
from cutty.variables.bindings import Binding
from cutty.variables.variables import GenericVariable


def test_renderbind_with_binddefault(
    variable: GenericVariable[str], render: Renderer
) -> None:
    """It binds variables using only defaults."""
    [binding] = renderbind(render, binddefault, [variable])

    assert binding.name == "project"
    assert binding.value == "example"


@pytest.mark.parametrize(
    "given,expected",
    [
        (Binding("project", "foobar"), Binding("project", "foobar")),
        (Binding("unrelated", "foobar"), Binding("project", "example")),
    ],
)
def test_renderbind_with_override(
    variable: GenericVariable[str], render: Renderer, given: Binding, expected: Binding
) -> None:
    """It binds variables using defaults, unless overridden."""
    binder = override(binddefault, [given])

    [binding] = renderbind(render, binder, [variable])

    assert binding == expected
