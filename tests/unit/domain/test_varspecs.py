"""Unit tests for cutty.domain.varspecs."""
import dataclasses

import pytest

from cutty.domain.renderables import Renderable
from cutty.domain.renderables import TrivialRenderable
from cutty.domain.varspecs import DefaultVariableBuilder
from cutty.domain.varspecs import render
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType


@pytest.fixture
def specification() -> VariableSpecification[Renderable[str]]:
    """Fixture with a renderable variable specification."""
    return VariableSpecification(
        name="project",
        description="The name of the project",
        type=VariableType.STRING,
        default=TrivialRenderable("example"),
        choices=(),
        interactive=True,
    )


def test_render(specification: VariableSpecification[Renderable[str]]) -> None:
    """It renders the default and choices fields."""
    renderedspec = render(specification, [])
    attributes = dataclasses.asdict(renderedspec)

    for name, value in attributes.items():
        if name not in ["default", "choices"]:
            assert value == getattr(specification, name)

    assert renderedspec.default == "example"
    assert renderedspec.choices == ()


def test_default_variable_builder(
    specification: VariableSpecification[Renderable[str]],
) -> None:
    """It builds variables using only defaults."""
    builder = DefaultVariableBuilder()

    [variable] = builder.build([specification])

    assert variable.name == "project"
    assert variable.value == "example"
