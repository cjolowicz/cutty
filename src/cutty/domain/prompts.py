"""Prompting the user for template variables."""
import abc
from collections.abc import Iterable
from typing import Generic

from cutty.domain.renderables import Renderable
from cutty.domain.variables import Value
from cutty.domain.variables import ValueT
from cutty.domain.variables import ValueT_co
from cutty.domain.variables import Variable
from cutty.domain.varspecs import VariableBuilder
from cutty.domain.varspecs import VariableSpecification


class Prompt(abc.ABC, Generic[ValueT_co]):
    """User prompt."""

    def __init__(self, specification: VariableSpecification[ValueT_co]) -> None:
        """Initialize."""
        self.specification = specification

    def prompt(self) -> Variable[ValueT_co]:
        """Ask the user for a value."""
        value = self.promptvalue()
        return Variable(self.specification.name, value)

    @abc.abstractmethod
    def promptvalue(self) -> ValueT_co:
        """Ask the user for a value."""


class PromptFactory(abc.ABC):
    """Given a variable specification, return a prompt."""

    @abc.abstractmethod
    def create(self, specification: VariableSpecification[ValueT]) -> Prompt[ValueT]:
        """Create a prompt."""


class PromptVariableBuilder(VariableBuilder):
    """Build variables by prompting the user."""

    def __init__(self, factory: PromptFactory) -> None:
        """Initialize."""
        self.factory = factory

    def build(
        self, specifications: Iterable[Renderable[VariableSpecification[Value]]]
    ) -> list[Variable[Value]]:
        """Build variables to the specifications."""
        variables: list[Variable[Value]] = []
        for specification in specifications:
            rendered = specification.render(variables)
            prompt = self.factory.create(rendered)
            variable = prompt.prompt()
            variables.append(variable)
        return variables
