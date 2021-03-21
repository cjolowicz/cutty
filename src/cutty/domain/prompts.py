"""Prompting the user for template bindings."""
import abc
from collections.abc import Iterable
from typing import Generic

from cutty.domain.bindings import Binding
from cutty.domain.bindings import Value
from cutty.domain.bindings import ValueT
from cutty.domain.bindings import ValueT_co
from cutty.domain.render import Renderer
from cutty.domain.variables import Binder
from cutty.domain.variables import Variable


class Prompt(abc.ABC, Generic[ValueT_co]):
    """User prompt."""

    def __init__(self, variable: Variable[ValueT_co]) -> None:
        """Initialize."""
        self.variable = variable

    def prompt(self) -> Binding[ValueT_co]:
        """Ask the user for a value."""
        value = self.promptvalue()
        return Binding(self.variable.name, value)

    @abc.abstractmethod
    def promptvalue(self) -> ValueT_co:
        """Ask the user for a value."""


class PromptFactory(abc.ABC):
    """Given a variable, return a prompt."""

    @abc.abstractmethod
    def create(self, variable: Variable[ValueT]) -> Prompt[ValueT]:
        """Create a prompt."""


class PromptBinder(Binder):
    """Bind variables by prompting the user."""

    def __init__(self, factory: PromptFactory) -> None:
        """Initialize."""
        self.factory = factory

    def bind(
        self,
        variables: Iterable[Variable[Value]],
        settings: Iterable[Binding[Value]],
        render: Renderer,
    ) -> list[Binding[Value]]:
        """Bind the variables."""
        settings = tuple(settings)
        bindings: list[Binding[Value]] = []
        for variable in variables:
            variable = render(variable, bindings, settings)
            prompt = self.factory.create(variable)
            binding = prompt.prompt()
            bindings.append(binding)
        return bindings
