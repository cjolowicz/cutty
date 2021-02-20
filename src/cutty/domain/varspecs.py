"""Specifications for template variables."""
import abc
from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Generic
from typing import TypeVar

from cutty.domain.renderables import Renderable
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


def render(
    specification: VariableSpecification[Renderable[ValueT_co]],
    variables: Sequence[Variable[Value]],
) -> VariableSpecification[ValueT_co]:
    """Render a variable specification."""
    return VariableSpecification(
        specification.name,
        specification.description,
        specification.type,
        specification.default.render(variables),
        tuple(choice.render(variables) for choice in specification.choices),
        specification.interactive,
    )


class VariableBuilder(abc.ABC):
    """Interface for building variables to specifications."""

    @abc.abstractmethod
    def build(
        self, specifications: Iterable[VariableSpecification[Renderable[Value]]]
    ) -> list[Variable[Value]]:
        """Build variables to the specifications."""


class DefaultVariableBuilder(VariableBuilder):
    """Build variables using only their defaults."""

    def build(
        self, specifications: Iterable[VariableSpecification[Renderable[Value]]]
    ) -> list[Variable[Value]]:
        """Build variables to the specifications."""
        variables: list[Variable[Value]] = []
        for specification in specifications:
            variable = Variable(
                specification.name,
                specification.default.render(variables),
            )
            variables.append(variable)
        return variables
