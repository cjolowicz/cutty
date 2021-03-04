"""Unit tests for cutty.domain.varspecs."""
import dataclasses

from cutty.domain.renderables import Renderable
from cutty.domain.varspecs import DefaultVariableBuilder
from cutty.domain.varspecs import VariableSpecification


def test_render(specification: Renderable[VariableSpecification[str]]) -> None:
    """It renders the default and choices fields."""
    rendered = specification.render([])
    attributes = dataclasses.asdict(rendered)

    for name, value in attributes.items():
        if name not in ["default", "choices"]:
            assert value == getattr(specification, name)

    assert rendered.default == "example"
    assert rendered.choices == ()


def test_default_variable_builder(
    specification: Renderable[VariableSpecification[str]],
) -> None:
    """It builds variables using only defaults."""
    builder = DefaultVariableBuilder()

    [variable] = builder.build([specification])

    assert variable.name == "project"
    assert variable.value == "example"
