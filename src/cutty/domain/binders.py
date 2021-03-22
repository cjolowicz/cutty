"""Binding variables."""
from collections.abc import Callable
from collections.abc import Sequence
from typing import Protocol

from cutty.domain.bindings import Binding
from cutty.domain.render import Renderer
from cutty.domain.variables import Variable


Bind = Callable[[Variable], Binding]


class Binder(Protocol):
    """Protocol for binding variables."""

    def __call__(
        self, variables: Sequence[Variable], *, render: Renderer
    ) -> Sequence[Binding]:
        """Bind the variables."""


def create_binder(bind: Bind) -> Binder:
    """Create a binder."""

    def _bind(variables: Sequence[Variable], *, render: Renderer) -> Sequence[Binding]:
        bindings: list[Binding] = []
        for variable in variables:
            variable = render(variable, bindings)
            binding = bind(variable)
            bindings.append(binding)
        return bindings

    return _bind


default_bind = create_binder(lambda variable: Binding(variable.name, variable.default))
