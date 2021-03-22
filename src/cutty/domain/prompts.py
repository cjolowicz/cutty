"""Prompting the user for template bindings."""
import abc
from typing import Generic

from cutty.domain.binders import Binder
from cutty.domain.binders import create_binder
from cutty.domain.bindings import Binding
from cutty.domain.bindings import GenericBinding
from cutty.domain.values import ValueT
from cutty.domain.values import ValueT_co
from cutty.domain.variables import GenericVariable
from cutty.domain.variables import Variable


class Prompt(abc.ABC, Generic[ValueT_co]):
    """User prompt."""

    def __init__(self, variable: GenericVariable[ValueT_co]) -> None:
        """Initialize."""
        self.variable = variable

    def prompt(self) -> GenericBinding[ValueT_co]:
        """Ask the user for a value."""
        value = self.promptvalue()
        return GenericBinding(self.variable.name, value)

    @abc.abstractmethod
    def promptvalue(self) -> ValueT_co:
        """Ask the user for a value."""


class PromptFactory(abc.ABC):
    """Given a variable, return a prompt."""

    @abc.abstractmethod
    def create(self, variable: GenericVariable[ValueT]) -> Prompt[ValueT]:
        """Create a prompt."""


def create_prompt_binder(prompts: PromptFactory) -> Binder:
    """Bind variables by prompting the user."""

    def _prompt(variable: Variable) -> Binding:
        prompt = prompts.create(variable)
        return prompt.prompt()

    return create_binder(_prompt)
