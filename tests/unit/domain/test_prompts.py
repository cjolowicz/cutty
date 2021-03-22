"""Unit tests for cutty.domain.prompts."""
from cutty.domain.prompts import create_prompt_binder
from cutty.domain.prompts import Prompt
from cutty.domain.prompts import PromptFactory
from cutty.domain.render import Renderer
from cutty.domain.values import ValueT
from cutty.domain.values import ValueT_co
from cutty.domain.variables import GenericVariable


class FakePrompt(Prompt[ValueT_co]):
    """Prompt that returns the default instead of asking the user."""

    def promptvalue(self) -> ValueT_co:
        """Return the default."""
        return self.variable.default


class FakePromptFactory(PromptFactory):
    """Create fake prompts."""

    def create(self, variable: GenericVariable[ValueT]) -> Prompt[ValueT]:
        """Return a fake prompt."""
        return FakePrompt(variable)


def test_prompt_variable_binder(
    variable: GenericVariable[str], render: Renderer
) -> None:
    """It binds variables using the prompts."""
    factory = FakePromptFactory()
    bind = create_prompt_binder(factory)

    [binding] = bind([variable], render=render)

    assert binding.name == "project"
    assert binding.value == "example"
