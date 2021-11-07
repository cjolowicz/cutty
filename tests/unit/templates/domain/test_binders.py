"""Unit tests for cutty.templates.domain.binders."""
import pytest

from cutty.templates.domain.binders import renderbindwith
from cutty.templates.domain.render import Renderer
from cutty.variables.binders import binddefault
from cutty.variables.binders import override
from cutty.variables.bindings import Binding
from cutty.variables.variables import GenericVariable


def test_renderbind_with_binddefault(
    variable: GenericVariable[str], render: Renderer
) -> None:
    """It binds variables using only defaults."""
    renderbind = renderbindwith(binddefault)

    [binding] = renderbind(render, [variable])

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
    renderbind = renderbindwith(override(binddefault, [given]))

    [binding] = renderbind(render, [variable])

    assert binding == expected
