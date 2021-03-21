"""Unit tests for cutty.domain.prompts."""
from cutty.domain.bindings import ValueT
from cutty.domain.bindings import ValueT_co
from cutty.domain.prompts import Prompt
from cutty.domain.prompts import PromptBinder
from cutty.domain.prompts import PromptFactory
from cutty.domain.render import Renderer
from cutty.domain.variables import Variable


class FakePrompt(Prompt[ValueT_co]):
    """Prompt that returns the default instead of asking the user."""

    def promptvalue(self) -> ValueT_co:
        """Return the default."""
        return self.variable.default


class FakePromptFactory(PromptFactory):
    """Create fake prompts."""

    def create(self, variable: Variable[ValueT]) -> Prompt[ValueT]:
        """Return a fake prompt."""
        return FakePrompt(variable)


def test_prompt_variable_binder(variable: Variable[str], render: Renderer) -> None:
    """It binds variables using the prompts."""
    factory = FakePromptFactory()
    binder = PromptBinder(factory)

    [binding] = binder.bind([variable], [], render)

    assert binding.name == "project"
    assert binding.value == "example"
