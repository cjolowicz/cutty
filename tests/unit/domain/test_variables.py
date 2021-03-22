"""Unit tests for cutty.domain.variables."""
from cutty.domain.binders import renderbinddefault
from cutty.domain.render import Renderer
from cutty.domain.variables import GenericVariable


def test_render(variable: GenericVariable[str], render: Renderer) -> None:
    """It renders the variable."""
    assert variable == render(variable, [])


def test_renderbinddefault(variable: GenericVariable[str], render: Renderer) -> None:
    """It binds variables using only defaults."""
    [binding] = renderbinddefault(render, [variable])

    assert binding.name == "project"
    assert binding.value == "example"
