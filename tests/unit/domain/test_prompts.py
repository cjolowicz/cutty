"""Unit tests for cutty.domain.prompts."""
from cutty.domain.prompts import Prompt
from cutty.domain.prompts import PromptFactory
from cutty.domain.prompts import PromptVariableBuilder
from cutty.domain.renderables import Renderable
from cutty.domain.variables import ValueT
from cutty.domain.variables import ValueT_co
from cutty.domain.varspecs import VariableSpecification


class FakePrompt(Prompt[ValueT_co]):
    """Prompt that returns the default instead of asking the user."""

    def promptvalue(self) -> ValueT_co:
        """Return the default."""
        return self.specification.default


class FakePromptFactory(PromptFactory):
    """Create fake prompts."""

    def create(self, specification: VariableSpecification[ValueT]) -> Prompt[ValueT]:
        """Return a fake prompt."""
        return FakePrompt(specification)


def test_prompt_variable_builder(
    specification: Renderable[VariableSpecification[str]],
) -> None:
    """It builds variables using the prompts."""
    factory = FakePromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification])

    assert variable.name == "project"
    assert variable.value == "example"
