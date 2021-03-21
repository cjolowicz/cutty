"""Unit tests for cutty.domain.variables."""
from cutty.domain.render import Renderer
from cutty.domain.variables import DefaultBinder
from cutty.domain.variables import Variable


def test_render(variable: Variable[str], render: Renderer) -> None:
    """It renders the variable."""
    assert variable == render(variable, [], [])


def test_default_variable_binder(variable: Variable[str], render: Renderer) -> None:
    """It binds variables using only defaults."""
    binder = DefaultBinder()

    [binding] = binder.bind([variable], [], render)

    assert binding.name == "project"
    assert binding.value == "example"
