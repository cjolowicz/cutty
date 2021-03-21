"""Specifications for template variables."""
import abc
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Generic
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cutty.domain.render import Renderer
from cutty.domain.variables import Value
from cutty.domain.variables import ValueT_co
from cutty.domain.variables import Variable


class VariableType(str, Enum):
    """The kinds of values a template variable can hold."""

    NULL = "null"
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"
    ARRAY = "array"
    OBJECT = "object"


@dataclass(frozen=True)
class VariableSpecification(Generic[ValueT_co]):
    """Specification for a template variable."""

    name: str
    description: str
    type: VariableType
    default: ValueT_co
    choices: tuple[ValueT_co, ...]
    interactive: bool


class VariableBuilder(abc.ABC):
    """Interface for building variables to specifications."""

    @abc.abstractmethod
    def build(
        self,
        specifications: Iterable[VariableSpecification[Value]],
        settings: Iterable[Variable[Value]],
        render: Renderer,
    ) -> list[Variable[Value]]:
        """Build variables to the specifications."""


class DefaultVariableBuilder(VariableBuilder):
    """Build variables using only their defaults."""

    def build(
        self,
        specifications: Iterable[VariableSpecification[Value]],
        settings: Iterable[Variable[Value]],
        render: Renderer,
    ) -> list[Variable[Value]]:
        """Build variables to the specifications."""
        settings = tuple(settings)
        variables: list[Variable[Value]] = []
        for specification in specifications:
            rendered = render(specification, variables, settings)
            variable = Variable(rendered.name, rendered.default)
            variables.append(variable)
        return variables
