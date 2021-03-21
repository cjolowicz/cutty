"""Template variables."""
import abc
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cutty.domain.render import Renderer
from cutty.domain.bindings import Value
from cutty.domain.bindings import ValueT_co
from cutty.domain.bindings import ValueType
from cutty.domain.bindings import Binding


@dataclass(frozen=True)
class Variable(Generic[ValueT_co]):
    """Specification for a template variable."""

    name: str
    description: str
    type: ValueType
    default: ValueT_co
    choices: tuple[ValueT_co, ...]
    interactive: bool


class Binder(abc.ABC):
    """Interface for binding variables."""

    @abc.abstractmethod
    def bind(
        self,
        variables: Iterable[Variable[Value]],
        settings: Iterable[Binding],
        render: Renderer,
    ) -> list[Binding]:
        """Bind the variables."""


class DefaultBinder(Binder):
    """Bind variables using only their defaults."""

    def bind(
        self,
        variables: Iterable[Variable[Value]],
        settings: Iterable[Binding],
        render: Renderer,
    ) -> list[Binding]:
        """Bind the variables."""
        settings = tuple(settings)
        bindings: list[Binding] = []
        for variable in variables:
            variable = render(variable, bindings, settings)
            binding = Binding(variable.name, variable.default)
            bindings.append(binding)
        return bindings
