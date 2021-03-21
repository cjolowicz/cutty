"""Binding variables."""
import abc
from collections.abc import Sequence

from cutty.domain.bindings import Binding
from cutty.domain.render import Renderer
from cutty.domain.variables import Variable


class Binder(abc.ABC):
    """Interface for binding variables."""

    @abc.abstractmethod
    def bind(
        self,
        variables: Sequence[Variable],
        settings: Sequence[Binding],
        render: Renderer,
    ) -> Sequence[Binding]:
        """Bind the variables."""


class DefaultBinder(Binder):
    """Bind variables using only their defaults."""

    def bind(
        self,
        variables: Sequence[Variable],
        settings: Sequence[Binding],
        render: Renderer,
    ) -> Sequence[Binding]:
        """Bind the variables."""
        bindings: list[Binding] = []
        for variable in variables:
            variable = render(variable, bindings)
            binding = Binding(variable.name, variable.default)
            bindings.append(binding)
        return bindings
