"""Unit tests for cutty.templates.domain.binders."""
import pytest

from cutty.templates.domain.binders import binddefault
from cutty.templates.domain.binders import override
from cutty.templates.domain.binders import renderbindwith
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.variables import GenericVariable


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


def test_override_empty(variable: GenericVariable[str]) -> None:
    """It does not override the variable."""
    binder = override(binddefault, [])
    binding = binder(variable)

    assert binding.name == variable.name
    assert binding.value == variable.default
