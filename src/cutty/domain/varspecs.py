"""Specifications for template variables."""
import abc
from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Generic
from typing import TypeVar

from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.renderables import RenderableValueLoader
from cutty.domain.variables import Value
from cutty.domain.variables import ValueT_co
from cutty.domain.variables import Variable


T_co = TypeVar("T_co", covariant=True)


class VariableType(str, Enum):
    """The kinds of values a template variable can hold."""

    NULL = "null"
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"
    ARRAY = "array"
    OBJECT = "object"


@dataclass(frozen=True)
class VariableSpecification(Generic[T_co]):
    """Specification for a template variable."""

    name: str
    description: str
    type: VariableType
    default: T_co
    choices: tuple[T_co, ...]
    interactive: bool


class RenderableVariableSpecification(
    Renderable[VariableSpecification[ValueT_co]],
    VariableSpecification[Renderable[ValueT_co]],
):
    """A renderable specification for a template variable."""

    def render(
        self,
        variables: Sequence[Variable[Value]],
    ) -> VariableSpecification[ValueT_co]:
        """Render a variable specification."""
        return VariableSpecification(
            self.name,
            self.description,
            self.type,
            self.default.render(variables),
            tuple(choice.render(variables) for choice in self.choices),
            self.interactive,
        )


class RenderableVariableSpecificationLoader(
    RenderableLoader[VariableSpecification[Value]]
):
    """A loader for renderable variable specifications."""

    def __init__(self, loader: RenderableLoader[str]) -> None:
        """Initialize."""
        self.loader = RenderableValueLoader(loader)

    def load(
        self, value: VariableSpecification[Value]
    ) -> Renderable[VariableSpecification[Value]]:
        """Load the renderable."""
        return RenderableVariableSpecification(
            value.name,
            value.description,
            value.type,
            self.loader.load(value.default),
            tuple(self.loader.load(choice) for choice in value.choices),
            value.interactive,
        )


class VariableBuilder(abc.ABC):
    """Interface for building variables to specifications."""

    @abc.abstractmethod
    def build(
        self, specifications: Iterable[Renderable[VariableSpecification[Value]]]
    ) -> list[Variable[Value]]:
        """Build variables to the specifications."""


class DefaultVariableBuilder(VariableBuilder):
    """Build variables using only their defaults."""

    def build(
        self, specifications: Iterable[Renderable[VariableSpecification[Value]]]
    ) -> list[Variable[Value]]:
        """Build variables to the specifications."""
        variables: list[Variable[Value]] = []
        for specification in specifications:
            rendered = specification.render(variables)
            variable = Variable(rendered.name, rendered.default)
            variables.append(variable)
        return variables
