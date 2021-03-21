"""Unit tests for cutty.domain.varspecs."""
from cutty.domain.render import Renderer
from cutty.domain.varspecs import DefaultVariableBuilder
from cutty.domain.varspecs import VariableSpecification


def test_render(specification: VariableSpecification[str], render: Renderer) -> None:
    """It renders the default and choices fields."""
    rendered = render(specification, [], [])
    assert rendered == specification


def test_default_variable_builder(
    specification: VariableSpecification[str], render: Renderer
) -> None:
    """It builds variables using only defaults."""
    builder = DefaultVariableBuilder()

    [variable] = builder.build([specification], [], render)

    assert variable.name == "project"
    assert variable.value == "example"
