"""Unit tests for cutty.domain.variables."""
from cutty.domain.binders import default_bind
from cutty.domain.render import Renderer
from cutty.domain.variables import GenericVariable


def test_render(variable: GenericVariable[str], render: Renderer) -> None:
    """It renders the variable."""
    assert variable == render(variable, [])


def test_default_variable_binder(
    variable: GenericVariable[str], render: Renderer
) -> None:
    """It binds variables using only defaults."""
    [binding] = default_bind([variable], render=render)

    assert binding.name == "project"
    assert binding.value == "example"
