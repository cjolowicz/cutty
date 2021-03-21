"""Prompting the user for template bindings."""
import abc
from collections.abc import Sequence
from typing import Generic

from cutty.domain.binders import Binder
from cutty.domain.bindings import Binding
from cutty.domain.bindings import GenericBinding
from cutty.domain.render import Renderer
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


class PromptBinder(Binder):
    """Bind variables by prompting the user."""

    def __init__(self, factory: PromptFactory) -> None:
        """Initialize."""
        self.factory = factory

    def bind(
        self, variables: Sequence[Variable], render: Renderer
    ) -> Sequence[Binding]:
        """Bind the variables."""
        bindings: list[Binding] = []
        for variable in variables:
            variable = render(variable, bindings)
            prompt = self.factory.create(variable)
            binding = prompt.prompt()
            bindings.append(binding)
        return bindings
