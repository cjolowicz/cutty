"""Binding variables."""
from collections.abc import Sequence
from typing import Protocol

from cutty.domain.bindings import Binding
from cutty.domain.render import Renderer
from cutty.domain.variables import Variable


class Binder(Protocol):
    """Protocol for binding variables."""

    def __call__(
        self, variables: Sequence[Variable], *, render: Renderer
    ) -> Sequence[Binding]:
        """Bind the variables."""


def bind_default(
    variables: Sequence[Variable], *, render: Renderer
) -> Sequence[Binding]:
    """Bind variables using only their defaults."""
    bindings: list[Binding] = []
    for variable in variables:
        variable = render(variable, bindings)
        binding = Binding(variable.name, variable.default)
        bindings.append(binding)
    return bindings
