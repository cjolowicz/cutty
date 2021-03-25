"""Unit tests for cutty.domain.variables."""
from cutty.domain.binders import binddefault
from cutty.domain.binders import renderbindwith
from cutty.domain.render import Renderer
from cutty.domain.variables import GenericVariable


def test_render(variable: GenericVariable[str], render: Renderer) -> None:
    """It renders the variable."""
    assert variable == render(variable, [])


def test_renderbind_with_binddefault(
    variable: GenericVariable[str], render: Renderer
) -> None:
    """It binds variables using only defaults."""
    renderbind = renderbindwith(binddefault)

    [binding] = renderbind(render, [variable])

    assert binding.name == "project"
    assert binding.value == "example"
